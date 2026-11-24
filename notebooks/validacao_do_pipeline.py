# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Validação do pipeline
# MAGIC %md
# MAGIC # Validação do pipeline Sismos × Clima
# MAGIC Confere, camada por camada, o resultado da última execução do job e serve de roteiro da apresentação técnica. **Todas as células só leem**: nenhuma chama API, grava tabela ou regrava arquivo. Pode usar **Run all**.
# MAGIC
# MAGIC **Antes de começar**
# MAGIC 1. Compute deste notebook: **Serverless** (ele mistura SQL e Python; SQL warehouse não roda Python).
# MAGIC 2. Dispare o pipeline em **Jobs & Pipelines → ft03-sismos-clima-pipeline → Run now** (cerca de 5 minutos). As consultas leem o resultado da última execução.
# MAGIC
# MAGIC | Parte | Assunto |
# MAGIC |---|---|
# MAGIC | 1 | Abertura |
# MAGIC | 2 | Arquitetura: o que existe em cada camada |
# MAGIC | 3 | Extração resiliente |
# MAGIC | 4 | Bronze e silver: desaninhamento em SQL |
# MAGIC | 5 | Gold: JOIN e métricas |
# MAGIC | 6 | Qualidade e teste negativo |
# MAGIC | 7 | Exportação e prova do Snappy |
# MAGIC | 8 | Resultado do job e falha controlada |

# COMMAND ----------

# DBTITLE 1,Fixar fuso UTC
# MAGIC %sql
# MAGIC SET TIME ZONE 'UTC';  -- horas exibidas em UTC, como nas tabelas

# COMMAND ----------

# DBTITLE 1,Parte 1 · Abertura
# MAGIC %md
# MAGIC ## Parte 1 · Abertura
# MAGIC **Falar:**
# MAGIC - Pergunta: como estava o clima no epicentro, hora a hora, no dia de cada terremoto de magnitude 5 ou mais?
# MAGIC - Duas APIs públicas de domínios diferentes: **USGS** (sismologia) e **Open-Meteo** (meteorologia).
# MAGIC - Outubro de 2026: **224 sismos x 24 horas = 5.376 linhas**.
# MAGIC - Databricks Free Edition, serverless, Python e SQL, job de 7 tarefas.

# COMMAND ----------

# DBTITLE 1,Parte 2 · Arquitetura
# MAGIC %md
# MAGIC ## Parte 2 · Arquitetura: o que existe em cada camada
# MAGIC **Falar:** medalhão no Unity Catalog, um catálogo do projeto e um schema por camada.
# MAGIC - **bronze:** volume `raw` (JSON como a API devolveu: `usgs/` com 1 arquivo, `open_meteo/` com 1 arquivo por sismo e `extracao_relatorio.json`); `usgs_resposta` (1 linha com a lista `features` de 224 sismos); `meteo_resposta` (1 linha por sismo, com listas paralelas em `hourly`).
# MAGIC - **silver:** `sismos` (1 linha por sismo, 12 colunas) e `clima_horario` (1 linha por sismo e hora, 10 colunas).
# MAGIC - **gold:** `sismo_clima_horario` (22 colunas, partição ano/mês, Snappy), `qualidade_regras` (1 linha por regra SQL) e volume `export` (Parquet e relatório).

# COMMAND ----------

# DBTITLE 1,Tabelas por camada
# MAGIC %sql
# MAGIC SELECT table_schema AS camada, table_name AS tabela, table_type AS tipo  -- objetos do catálogo do projeto
# MAGIC FROM ft03_sismos_clima.information_schema.tables
# MAGIC WHERE table_schema IN ('bronze', 'silver', 'gold')  -- só as camadas do medalhão
# MAGIC ORDER BY CASE table_schema WHEN 'bronze' THEN 1 WHEN 'silver' THEN 2 ELSE 3 END, table_name;  -- na ordem do fluxo

# COMMAND ----------

# DBTITLE 1,Volumes por camada
# MAGIC %sql
# MAGIC SELECT volume_schema AS camada, volume_name AS volume, volume_type AS tipo  -- pastas de arquivos do Unity Catalog
# MAGIC FROM ft03_sismos_clima.information_schema.volumes
# MAGIC ORDER BY volume_schema;  -- bronze.raw e gold.export

# COMMAND ----------

# DBTITLE 1,Parte 3 · Extração resiliente
# MAGIC %md
# MAGIC ## Parte 3 · Extração resiliente
# MAGIC Código: `notebooks/01_extracao_bronze` e `src/sismos_clima/http_client.py` (mostrar sem executar).
# MAGIC
# MAGIC **Falar:**
# MAGIC - `count` antes da `query`: a USGS aceita até 20.000 eventos por consulta.
# MAGIC - 1 `count` + 1 `query` + 1 chamada de clima por sismo = **226 chamadas**.
# MAGIC - **Controle de taxa** (`LimitadorTaxa`): 1 s entre chamadas à USGS (limite não publicado) e 0,5 s ao Open-Meteo (publica 600 por minuto).
# MAGIC - **Retentativa** (`ClienteHttp`): só 429, 500, 502, 503, 504 e timeout; até 5 vezes, espera 1, 2, 4, 8 s com variação; respeita `Retry-After`. 400 não repete.
# MAGIC - `limpar_raw` apaga os JSON da execução anterior **depois** que a USGS responde: sem isso a bronze misturava períodos (erro real, corrigido).

# COMMAND ----------

# DBTITLE 1,Relatório da extração
# MAGIC %sql
# MAGIC SELECT count_usgs, chamadas, climas_gravados, arquivos_antigos_removidos, completo, falhas, duracao_s, periodo  -- números da extração
# MAGIC FROM read_files(
# MAGIC   '/Volumes/ft03_sismos_clima/bronze/raw/extracao_relatorio.json',  -- gravado pela tarefa extracao
# MAGIC   format => 'json'  -- objeto JSON numa linha só
# MAGIC );

# COMMAND ----------

# DBTITLE 1,Parte 4 · Bronze e silver
# MAGIC %md
# MAGIC ## Parte 4 · Bronze e silver: desaninhamento em SQL
# MAGIC Código: `sql/silver/01_silver` (mostrar `explode(features)` e `LATERAL VIEW posexplode(hourly.time)`).
# MAGIC
# MAGIC **Falar:**
# MAGIC - A USGS é **uma linha só** com 224 sismos numa lista; `explode` vira 224 linhas.
# MAGIC - O Open-Meteo manda **listas paralelas** (horas, temperatura, umidade...); `posexplode` cria uma linha por hora e guarda a posição para ler as outras listas.
# MAGIC - Silver: **T1** tipos e datas, **T2** nulos (linha sem chave, horário, magnitude ou coordenada é rejeitada), **T3** deduplicação (versão mais recente).

# COMMAND ----------

# DBTITLE 1,Sismos: da lista para as linhas
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT count(*) FROM ft03_sismos_clima.bronze.usgs_resposta) AS linhas_na_bronze,  -- arquivos da USGS
# MAGIC   (SELECT size(features) FROM ft03_sismos_clima.bronze.usgs_resposta) AS sismos_dentro_da_lista,  -- itens da lista features
# MAGIC   (SELECT count(*) FROM ft03_sismos_clima.silver.sismos) AS linhas_na_silver;  -- uma linha por sismo depois do explode

# COMMAND ----------

# DBTITLE 1,Clima ainda aninhado na bronze
# MAGIC %sql
# MAGIC SELECT
# MAGIC   slice(hourly.time, 1, 3) AS horas,  -- 3 primeiros itens da lista de horas
# MAGIC   slice(hourly.temperature_2m, 1, 3) AS temperaturas,  -- 3 primeiros itens da lista de temperatura
# MAGIC   slice(hourly.relative_humidity_2m, 1, 3) AS umidades  -- 3 primeiros itens da lista de umidade
# MAGIC FROM ft03_sismos_clima.bronze.meteo_resposta
# MAGIC WHERE _arquivo LIKE '%/us6000tyny.json';  -- o id do sismo está no nome do arquivo

# COMMAND ----------

# DBTITLE 1,O mesmo clima aberto em linhas na silver
# MAGIC %sql
# MAGIC SELECT hora_utc, temperatura_c, umidade_pct  -- uma linha por hora
# MAGIC FROM ft03_sismos_clima.silver.clima_horario
# MAGIC WHERE evento_id = 'us6000tyny'  -- mesmo sismo da célula anterior
# MAGIC ORDER BY hora_utc  -- da primeira hora em diante
# MAGIC LIMIT 3;  -- só as 3 primeiras

# COMMAND ----------

# DBTITLE 1,Parte 5 · Gold
# MAGIC %md
# MAGIC ## Parte 5 · Gold: JOIN e métricas
# MAGIC Código: `sql/gold/01_gold` (mostrar o `INNER JOIN ... ON evento_id`, o `PARTITIONED BY (ano, mes)` e o `TBLPROPERTIES`).
# MAGIC
# MAGIC **Falar:**
# MAGIC - JOIN pelo **id do sismo**, não pela coordenada: o Open-Meteo ajusta o ponto à grade (mandei 36,1078, voltou 36,098415).
# MAGIC - Métricas: `horas_desde_sismo`, `periodo` (antes, hora do sismo, depois), `faixa_magnitude`, média, amplitude e chuva do dia.
# MAGIC - A tabela gerenciada nasce com ZSTD; o Snappy foi declarado na tabela. A prova no arquivo vem na Parte 7.

# COMMAND ----------

# DBTITLE 1,O JOIN não multiplicou nem perdeu linhas
# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT count(*) FROM ft03_sismos_clima.silver.sismos) AS sismos,  -- lado esquerdo do JOIN
# MAGIC   (SELECT count(*) FROM ft03_sismos_clima.silver.clima_horario) AS horas_de_clima,  -- lado direito do JOIN
# MAGIC   (SELECT count(*) FROM ft03_sismos_clima.gold.sismo_clima_horario) AS linhas_na_gold,  -- resultado do JOIN
# MAGIC   (SELECT count(DISTINCT evento_id, hora_utc) FROM ft03_sismos_clima.gold.sismo_clima_horario) AS pares_unicos;  -- chave da gold sem repetição

# COMMAND ----------

# DBTITLE 1,A virada antes e depois do sismo
# MAGIC %sql
# MAGIC SELECT evento_id, instante_sismo_utc, hora_utc, horas_desde_sismo, periodo,  -- quando foi o sismo e qual hora é esta
# MAGIC        temperatura_c, temp_media_dia_c, amplitude_termica_dia_c, precipitacao_total_dia_mm  -- clima da hora e métricas do dia
# MAGIC FROM ft03_sismos_clima.gold.sismo_clima_horario
# MAGIC WHERE evento_id = 'aka2026tuxgky'  -- sismo de 06/10/2026, magnitude 5,5
# MAGIC   AND horas_desde_sismo BETWEEN -1 AND 1  -- uma hora antes, a hora do sismo e uma hora depois
# MAGIC ORDER BY hora_utc;

# COMMAND ----------

# DBTITLE 1,Snappy registrado na tabela gold
# MAGIC %sql
# MAGIC SHOW TBLPROPERTIES ft03_sismos_clima.gold.sismo_clima_horario ('delta.parquet.compression.codec');  -- só a propriedade de compressão

# COMMAND ----------

# DBTITLE 1,Parte 6 · Qualidade
# MAGIC %md
# MAGIC ## Parte 6 · Qualidade e teste negativo
# MAGIC Código: `sql/quality/02_regras` e `src/sismos_clima/quality.py`.
# MAGIC
# MAGIC **Falar:**
# MAGIC - 15 regras: 10 em SQL e 5 em Python (schema das 3 tabelas, taxa de nulos do clima, silver igual ao `count` da USGS).
# MAGIC - Só a Q-03 é aviso; as outras são erro e bloqueiam a publicação.
# MAGIC - O relatório é gravado **antes** da decisão: se uma regra de erro reprovar, a tarefa falha, o Parquet não é publicado e o relatório explica o motivo.
# MAGIC - Zero violações não prova que a regra funciona: o **teste negativo** aplica a mesma conta a dados inventados com defeito.

# COMMAND ----------

# DBTITLE 1,As 15 regras do relatório
# MAGIC %sql
# MAGIC SELECT r.regra_id, r.tipo, r.nivel, r.verificados, r.violacoes, r.status  -- uma linha por regra
# MAGIC FROM read_files(
# MAGIC   '/Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json',  -- gravado pela tarefa relatorio
# MAGIC   format => 'json', multiLine => true  -- o arquivo tem várias linhas (JSON com recuo)
# MAGIC )
# MAGIC LATERAL VIEW explode(regras) t AS r  -- abre a lista de regras, o mesmo desaninhamento da silver
# MAGIC ORDER BY r.regra_id;

# COMMAND ----------

# DBTITLE 1,Resumo e decisão do relatório
# MAGIC %sql
# MAGIC SELECT iniciado_em_utc, resumo, aprovado, contagens, rejeitados  -- o que decide a publicação
# MAGIC FROM read_files(
# MAGIC   '/Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json',
# MAGIC   format => 'json', multiLine => true
# MAGIC );

# COMMAND ----------

# DBTITLE 1,Teste negativo de 6 regras
# MAGIC %sql
# MAGIC -- Mesma expressão de cada regra aplicada a linhas inventadas com defeito; 'detectou' = a regra acha o defeito
# MAGIC SELECT regra_id, encontradas, esperadas,  -- quanto a regra achou e quanto devia achar
# MAGIC   CASE WHEN encontradas = esperadas THEN 'detectou' ELSE 'falhou' END AS resultado  -- a regra funciona se os dois batem
# MAGIC FROM (
# MAGIC   SELECT 'Q-02' AS regra_id, count_if(evento_id IS NULL OR magnitude IS NULL) AS encontradas, 2 AS esperadas  -- 2 linhas com nulo
# MAGIC   FROM VALUES ('x', 1.0), (CAST(NULL AS STRING), 2.0), ('y', CAST(NULL AS DOUBLE)) AS t(evento_id, magnitude)
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-04', count(*) - count(DISTINCT evento_id), 1  -- 3 linhas e 2 ids distintos: 1 repetida
# MAGIC   FROM VALUES ('a'), ('a'), ('b') AS t(evento_id)
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-06', count_if(magnitude < 5), 2  -- 4.9 e 3.0 estão abaixo de 5
# MAGIC   FROM VALUES (4.9), (5.0), (3.0) AS t(magnitude)
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-07', count_if(latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180), 2  -- latitude 91 e longitude 181
# MAGIC   FROM VALUES (91.0, 0.0), (0.0, 181.0), (10.0, 20.0) AS t(latitude, longitude)
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-08', count_if(umidade_pct NOT BETWEEN 0 AND 100 OR precipitacao_mm < 0), 2  -- umidade 101 e chuva -1
# MAGIC   FROM VALUES (101.0, 0.0), (50.0, -1.0), (50.0, 0.0) AS t(umidade_pct, precipitacao_mm)
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-12', count_if(CAST(hora_utc AS DATE) <> data_utc), 1  -- a segunda hora já é do dia 02
# MAGIC   FROM VALUES (TIMESTAMP'2026-10-01 23:00:00', DATE'2026-10-01'), (TIMESTAMP'2026-10-02 00:00:00', DATE'2026-10-01') AS t(hora_utc, data_utc)
# MAGIC )
# MAGIC ORDER BY regra_id;

# COMMAND ----------

# DBTITLE 1,Teste negativo de Q-05a, Q-05b, Q-09 e Q-11
# MAGIC %sql
# MAGIC WITH clima_teste AS (  -- Q-05a: 4 horas de clima, com o par (a, 00:00) repetido
# MAGIC   SELECT * FROM VALUES ('a', TIMESTAMP'2026-10-01 00:00:00'), ('a', TIMESTAMP'2026-10-01 00:00:00'), ('a', TIMESTAMP'2026-10-01 01:00:00'), ('b', TIMESTAMP'2026-10-01 00:00:00') AS t(evento_id, hora_utc)
# MAGIC ),
# MAGIC gold_pares_teste AS (  -- Q-05b: a hora 10:00 do sismo c aparece 3 vezes
# MAGIC   SELECT * FROM VALUES ('c', TIMESTAMP'2026-10-01 10:00:00'), ('c', TIMESTAMP'2026-10-01 10:00:00'), ('c', TIMESTAMP'2026-10-01 10:00:00'), ('d', TIMESTAMP'2026-10-01 10:00:00') AS t(evento_id, hora_utc)
# MAGIC ),
# MAGIC gold_horas_teste AS (  -- Q-09 e Q-11: sismo a com 24 horas, b com 23 e c com 25
# MAGIC   SELECT 'a' AS evento_id, explode(sequence(0, 23)) AS hora  -- 24 linhas
# MAGIC   UNION ALL SELECT 'b', explode(sequence(0, 22))  -- 23 linhas (falta 1 hora)
# MAGIC   UNION ALL SELECT 'c', explode(sequence(0, 24))  -- 25 linhas (sobra 1 hora)
# MAGIC ),
# MAGIC silver_teste AS (  -- Q-11: 4 sismos na silver; o d não chegou à gold
# MAGIC   SELECT * FROM VALUES ('a'), ('b'), ('c'), ('d') AS t(evento_id)
# MAGIC )
# MAGIC SELECT regra_id, encontradas, esperadas,  -- quanto a regra achou e quanto devia achar
# MAGIC   CASE WHEN encontradas = esperadas THEN 'detectou' ELSE 'falhou' END AS resultado
# MAGIC FROM (
# MAGIC   SELECT 'Q-05a' AS regra_id, count(*) - count(DISTINCT evento_id, hora_utc) AS encontradas, 1 AS esperadas FROM clima_teste  -- 1 par repetido
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-05b', count(*) - count(DISTINCT evento_id, hora_utc), 2 FROM gold_pares_teste  -- 2 pares repetidos
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-09', count(*), 2 FROM (SELECT evento_id FROM gold_horas_teste GROUP BY evento_id HAVING count(*) <> 24)  -- b e c
# MAGIC   UNION ALL
# MAGIC   SELECT 'Q-11',
# MAGIC     abs((SELECT count(*) FROM gold_horas_teste) - 24 * (SELECT count(*) FROM silver_teste))  -- |72 - 96| = 24
# MAGIC       + (SELECT count(*) FROM silver_teste AS s WHERE NOT EXISTS (SELECT 1 FROM gold_horas_teste AS g WHERE g.evento_id = s.evento_id)),  -- + 1 sismo sem clima
# MAGIC     25
# MAGIC )
# MAGIC ORDER BY regra_id;

# COMMAND ----------

# DBTITLE 1,Parte 7 · Exportação
# MAGIC %md
# MAGIC ## Parte 7 · Exportação e prova do Snappy
# MAGIC Código: `notebooks/05_exportacao` (`write.mode("overwrite").partitionBy("ano", "mes").option("compression", "snappy").parquet(...)`).
# MAGIC
# MAGIC **Falar:**
# MAGIC - Parquet particionado por ano e mês no volume `gold.export`; os arquivos que começam com `_` são o controle de transação do Databricks.
# MAGIC - O Parquet tem as mesmas 5.376 linhas da gold; dentro do arquivo são 20 colunas, porque `ano` e `mes` ficam no nome das pastas.
# MAGIC - O nome `.snappy.parquet` não prova nada: a prova é o rodapé do arquivo, onde o Parquet registra a compressão de cada coluna.

# COMMAND ----------

# DBTITLE 1,Ler o Parquet exportado
# MAGIC %sql
# MAGIC SELECT ano, mes,  -- vêm do nome das pastas (ano=2026/mes=10)
# MAGIC        count(*) AS linhas,  -- linhas no Parquet
# MAGIC        count(DISTINCT _metadata.file_path) AS arquivos  -- quantos arquivos .parquet foram lidos
# MAGIC FROM read_files('/Volumes/ft03_sismos_clima/gold/export/dataset/', format => 'parquet')  -- lê a pasta do dataset
# MAGIC GROUP BY ano, mes;

# COMMAND ----------

# DBTITLE 1,Arquivos gravados e prova do Snappy no rodapé
from pathlib import Path  # caminhos de arquivo; o volume aparece como pasta local
import pyarrow.parquet as pq  # lê os metadados gravados no rodapé de arquivos Parquet

destino = Path("/Volumes/ft03_sismos_clima/gold/export/dataset")  # pasta do dataset no volume de exportação
for arquivo in sorted(p for p in destino.rglob("*") if p.is_file()):  # todos os arquivos, inclusive os de controle
    print(arquivo.relative_to(destino), arquivo.stat().st_size, "bytes")  # partição, nome e tamanho

codecs = set()  # compressões encontradas em todas as colunas de todos os arquivos
for arquivo in sorted(destino.rglob("*.parquet")):  # só os arquivos de dados
    meta = pq.ParquetFile(str(arquivo)).metadata  # rodapé do arquivo
    for i in range(meta.num_row_groups):  # cada grupo de linhas
        for j in range(meta.row_group(i).num_columns):  # cada coluna do grupo
            codecs.add(meta.row_group(i).column(j).compression)  # compressão registrada para a coluna
    print(arquivo.name, "| linhas:", meta.num_rows, "| colunas:", meta.num_columns, "| formato:", meta.format_version)  # resumo do rodapé
print("compressões no rodapé:", codecs)  # esperado {'SNAPPY'}

# COMMAND ----------

# DBTITLE 1,Parte 8 · Resultado e falha controlada
# MAGIC %md
# MAGIC ## Parte 8 · Resultado do job e falha controlada
# MAGIC **Mostrar:** Jobs & Pipelines → ft03-sismos-clima-pipeline → execução de hoje.
# MAGIC - Aba **List**: as 7 tarefas `Succeeded`, a duração de cada uma e a coluna **Depends on** (a cadeia extracao → ... → exportacao).
# MAGIC - Aba **Timeline**: a extração ocupa cerca de metade do tempo, por causa do intervalo entre chamadas.
# MAGIC - Painel **Parameters** da tarefa: os valores recebidos, com a marca `(resolved)`.
# MAGIC
# MAGIC **Falha controlada (opcional, cerca de 2 minutos):** seta ao lado de **Run now** → **Run now with different parameters** → `data_inicio` = `2026-10-31` e `data_fim` = `2026-10-01` → Run.
# MAGIC - A tarefa `extracao` falha no primeiro passo (período invertido), antes de chamar as APIs; as outras 6 não rodam. Nada é alterado.
# MAGIC - **Falar:** o pipeline para cedo e com mensagem clara; pelo terminal, o `run.sh` devolve código 1 nesse caso.
# FT03 – Sismos × Clima no Databricks

> **Status (24/11/2026):** pipeline completo no Databricks Free Edition. Um comando (`run.sh`) roda as 7 tarefas do job, das duas APIs até o Parquet Snappy particionado, e a última execução terminou com 15 de 15 regras de qualidade aprovadas. O dataset e o relatório estão em `output/`. O que ainda não foi testado está marcado como **A validar**.

Segunda entrega do **Desafio Python, FT03, Projeto 1**, com outro tema. É independente do projeto [`ft03-pipeline-energia-clima`](https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima).

## 1. Objetivo
Cruzar **terremotos de magnitude 5 ou mais** (USGS) com o **clima horário no epicentro, no dia UTC do sismo** (Open-Meteo Historical), em arquitetura medalhão (bronze, silver, gold) no Unity Catalog do Databricks Free Edition, com Python e SQL.

Pergunta que o dataset responde: como estavam temperatura, umidade, chuva, vento e pressão no epicentro, hora a hora, no dia de cada sismo, antes e depois do horário do evento. Não faz análise de causalidade entre sismo e clima.

## 2. APIs utilizadas
| API | Domínio | Endpoint | Autenticação | Limites publicados |
|---|---|---|---|---|
| USGS Earthquake Catalog (FDSN Event) | Sismologia | `https://earthquake.usgs.gov/fdsnws/event/1/query` e `/count` | não exige | até **20.000 eventos por consulta**; acima disso HTTP 400 (docs.html, consultado 23/11/2026). Limite de taxa numérico **não publicado**; excesso devolve HTTP 429 (aviso da lista realtime-feeds, jan/2022) |
| Open-Meteo Historical Weather | Meteorologia | `https://archive-api.open-meteo.com/v1/archive` | não exige (plano gratuito) | **600/min, 5.000/h, 10.000/dia, 300.000/mês**; consulta com mais de 10 variáveis ou mais de 2 semanas conta como várias chamadas; só uso não comercial; CC BY 4.0 (open-meteo.com/en/terms e /en/pricing, consultado 23/11/2026) |

Chamadas por execução: 1 `count` e 1 `query` na USGS e 1 chamada ao Open-Meteo por sismo (1 dia, 5 variáveis). Para outubro de 2026: 224 sismos, 226 chamadas. Saída de rede do Free Edition para os dois domínios: liberada em teste real (23/11/2026). Detalhes em `docs/03-tecnico/fontes-de-dados.md`.

## 3. Arquitetura e fluxo
```
USGS (GeoJSON) ─┐                          ┌─> silver.sismos         (explode de features[])
                ├─> volume bronze.raw ─────┤
Open-Meteo ─────┘   (JSON bruto)           └─> silver.clima_horario  (posexplode dos arrays hourly)
                         │                              │
                bronze.usgs_resposta          gold.sismo_clima_horario (JOIN por evento_id + métricas)
                bronze.meteo_resposta                   │
                                   gold.qualidade_regras + quality_report.json
                                                        │
                                   gold.export/dataset (Parquet Snappy, ano/mes) ──> output/
```

Job `ft03-sismos-clima-pipeline` (`jobs/ft03_pipeline.json`), 7 tarefas em sequência, em serverless:

| Tarefa | Notebook | O que faz |
|---|---|---|
| `extracao` | `notebooks/01_extracao_bronze` | Chama as APIs com controle de taxa e retentativas e grava o JSON bruto no volume `bronze.raw` |
| `bronze` | `sql/bronze/01_bronze` | Lê os JSON com `read_files` sem transformar |
| `silver` | `sql/silver/01_silver` | Desaninha em SQL e aplica tipos, nulos e deduplicação |
| `gold` | `sql/gold/01_gold` | JOIN e métricas; tabela particionada por ano e mês, com Snappy |
| `regras` | `sql/quality/02_regras` | 10 regras de qualidade em SQL, gravadas em `gold.qualidade_regras` |
| `relatorio` | `notebooks/04_qualidade` | Schema, nulos e contagens em Python; grava o relatório e para o job se uma regra de erro reprovar |
| `exportacao` | `notebooks/05_exportacao` | Só roda com a qualidade aprovada; grava o Parquet Snappy particionado e prova o Snappy no rodapé |

| Caminho | Conteúdo |
|---|---|
| `src/sismos_clima/` | Pacote Python modular e tipado: `config`, `http_client`, `extract`, `quality` |
| `notebooks/` | Notebooks Python do job |
| `sql/` | Notebooks SQL de bronze, silver, gold e qualidade |
| `jobs/` | Definição do job e corpos do `run-now` |
| `tests/` | 34 testes com pytest e amostras em `fixtures/` |
| `output/` | Dataset final em Parquet e relatório de qualidade |
| `docs/` | Gestão, negócio, arquitetura e fontes |

## 4. Requisitos de ambiente
| Item | Versão usada nos testes |
|---|---|
| Conta Databricks Free Edition (serverless) com saída de rede para os dois domínios | workspace testado em 23 e 24/11/2026 |
| Databricks CLI (mínimo 0.218 para os comandos usados) | 1.17.0 |
| Git e bash (Linux, macOS ou Git Bash no Windows) | Git para Windows |
| Python e pip, só para os testes locais | Python 3.10.12 |

## 5. Instalação (uma vez)
1. **Autenticar a CLI** no workspace (OAuth, sem token no disco do projeto):
   ```bash
   databricks auth login --host https://<seu-workspace>.cloud.databricks.com --profile ft03
   ```
2. **Criar catálogo, schemas e volumes** no SQL editor do workspace:
   ```sql
   CREATE CATALOG ft03_sismos_clima;
   CREATE SCHEMA ft03_sismos_clima.bronze;
   CREATE SCHEMA ft03_sismos_clima.silver;
   CREATE SCHEMA ft03_sismos_clima.gold;
   CREATE VOLUME ft03_sismos_clima.bronze.raw;
   CREATE VOLUME ft03_sismos_clima.gold.export;
   ```
3. **Criar um Git folder** no workspace a partir deste repositório (branch `main`). Os notebooks do job são lidos dele. Regra: editar arquivos no computador e, no Databricks, só fazer Pull e executar.
4. **Criar o job.** Copie `jobs/ft03_pipeline.json` para `jobs/ft03_pipeline.local.json` e troque `{{RAIZ_GIT}}` pelo caminho do Git folder (por exemplo `/Workspace/Users/<seu e-mail>/<pasta>/ft03-sismos-clima-databricks`). O `.gitignore` mantém os `*.local.json` fora do Git, porque o caminho tem o e-mail. Depois:
   ```bash
   databricks jobs create --json @jobs/ft03_pipeline.local.json -p ft03
   ```
   A resposta traz o `job_id`. Coloque esse número em `jobs/run_padrao.json`.

## 6. Variáveis de ambiente e parâmetros
As duas APIs não usam chave e nenhum segredo é versionado. A CLI se autentica pelo perfil criado no passo 5.1.

Parâmetros do job (`jobs/ft03_pipeline.json`), lidos pelos notebooks Python como widgets:

| Parâmetro | Padrão | Uso |
|---|---|---|
| `data_inicio` | `2026-10-01` | primeiro dia do período (UTC) |
| `data_fim` | `2026-10-31` | último dia, inclusive |
| `magnitude_minima` | `5` | filtro da USGS |
| `catalogo` | `ft03_sismos_clima` | catálogo do Unity Catalog nos notebooks Python |

Para outro período, envie `job_parameters` no corpo do `run-now`, como em `jobs/teste_a5_parametros.json`:
```bash
databricks jobs run-now --json @jobs/teste_a5_parametros.json -p ft03
```

`.env.example` lista as variáveis que `src/sismos_clima/config.py` lê fora do notebook (`FT03_DATA_INICIO`, `FT03_DATA_FIM`, `FT03_MAGNITUDE_MINIMA`, `FT03_CATALOGO`), o `DATABRICKS_HOST` da CLI e `OPEN_METEO_APIKEY` (lida pela configuração, mas não enviada nas chamadas desta versão, que usa o plano gratuito). Copie para `.env` se precisar; o `.env` não é versionado.

## 7. Execução (comando único)
`run.sh` dispara o job com `jobs/run_padrao.json` e espera o fim.

| Sistema | Comando |
|---|---|
| Linux, macOS ou Git Bash | `bash run.sh` |
| Windows PowerShell | `& "C:\Program Files\Git\bin\bash.exe" run.sh` (o `bash` do Windows pode ser o do WSL, que não tem a CLI nem o perfil) |

Outro perfil: `PERFIL=outro bash run.sh`. Outro corpo do `run-now` (por exemplo com `job_parameters`): `bash run.sh jobs/teste_a5_parametros.json`. Resultado esperado: JSON da execução com `"result_state": "SUCCESS"`, 7 tarefas `SUCCESS` e código de saída 0. Se a execução não terminar em `SUCCESS`, o `run.sh` mostra `O job não terminou em SUCCESS.` e sai com 1, mesmo quando a CLI devolve 0 (OB-47). Última execução conferida: 281 s (24/11/2026). A saída mostra o e-mail do workspace: não salve no repositório.

Atualizar `output/` depois de uma execução:
```bash
databricks fs cp -r "dbfs:/Volumes/ft03_sismos_clima/gold/export/dataset" output/dataset --overwrite -p ft03
databricks fs cp "dbfs:/Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json" output/reports/quality_report.json --overwrite -p ft03
```

## 8. Testes
```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/python -m pytest tests               # Windows: .venv\Scripts\python -m pytest tests
```
Resultado em 24/11/2026: `34 passed` (cliente HTTP 8, extração 13, qualidade 13), sem chamada de rede. As 10 regras em SQL têm teste negativo no próprio notebook `sql/quality/02_regras` (dados inventados com defeito; todas `detectou`). Detalhes em `tests/README.md`.

## 9. Schema e granularidade
`gold.sismo_clima_horario`: **1 linha por sismo e hora UTC do dia do sismo** (24 por sismo). Chave: (`evento_id`, `hora_utc`). Outubro de 2026: 224 sismos, 5.376 linhas, 22 colunas.

| Colunas | Tipo | Origem |
|---|---|---|
| `evento_id`, `local` | STRING | USGS (`local` nulo vira `Não informado`) |
| `ano`, `mes` | INT | cálculo sobre `data_utc`; colunas de partição |
| `data_utc` | DATE | dia UTC do sismo |
| `instante_sismo_utc` | TIMESTAMP | USGS (`time` em ms) |
| `magnitude`, `latitude`, `longitude`, `profundidade_km` | DOUBLE | USGS |
| `hora_utc` | TIMESTAMP | Open-Meteo (`hourly.time`) |
| `temperatura_c`, `umidade_pct`, `precipitacao_mm`, `vento_kmh`, `pressao_hpa` | DOUBLE | Open-Meteo, ponto de grade mais próximo do epicentro |
| `faixa_magnitude`, `periodo` | STRING | cálculo: `5.0 a 5.9`, `6.0 a 6.9`, `7.0 ou mais`; `antes`, `hora do sismo`, `depois` |
| `horas_desde_sismo` | INT | cálculo: hora do clima menos a hora cheia do sismo |
| `temp_media_dia_c`, `amplitude_termica_dia_c`, `precipitacao_total_dia_mm` | DOUBLE | cálculo sobre as 24 horas do sismo |

Silver e bronze estão descritas em `docs/02-arquitetura/plano-detalhado.md`.

## 10. Transformações e qualidade
Desaninhamento em SQL (`sql/silver/01_silver.sql`): `explode(features)` para os sismos e `posexplode(hourly.time)`, usando a posição para ler os demais arrays paralelos do clima.

| # | Transformação | Onde |
|---|---|---|
| T1 | Tipos e datas: milissegundos e texto ISO para TIMESTAMP, números para DOUBLE | silver |
| T2 | Nulos: sem chave, instante, coordenada ou magnitude a linha é rejeitada; `local` nulo vira `Não informado`; variável climática nula continua nula | silver |
| T3 | Deduplicação: por `evento_id`, fica a versão de maior `atualizado_em`; no clima, por (`evento_id`, `hora_utc`) | silver |
| T4 | JOIN de `silver.sismos` com `silver.clima_horario` por `evento_id` | gold |
| T5 | Métricas: `horas_desde_sismo`, `periodo`, `faixa_magnitude`, média, amplitude e chuva total do dia | gold |

| Regras | O que verificam | Nível |
|---|---|---|
| Q-01a, Q-01b, Q-01c | colunas e tipos das 3 tabelas | erro |
| Q-02, Q-03 | nulos nos campos obrigatórios (erro) e taxa de nulos das 5 variáveis climáticas (aviso) | erro e aviso |
| Q-04, Q-05a, Q-05b | unicidade de `evento_id` e de (`evento_id`, `hora_utc`) | erro |
| Q-06, Q-07, Q-08 | intervalos: magnitude, latitude e longitude, umidade e precipitação | erro |
| Q-09, Q-10, Q-11 | completude: 24 horas por sismo, silver igual ao `count` da USGS, gold igual a sismos x 24 | erro |
| Q-12 | dia de `hora_utc` igual a `data_utc` | erro |

Relatório: `quality_report.json` com id e horário da execução, período, contagens por camada, rejeitados, resultado de cada regra, nulos por coluna e estatísticas do clima. Política de falha: o relatório é gravado primeiro; se uma regra de nível erro reprovar, a tarefa `relatorio` falha e a `exportacao` não roda.

## 11. Particionamento e reprocessamento
- **Particionamento:** a gold é `PARTITIONED BY (ano, mes)` com `delta.parquet.compression.codec = SNAPPY`. A exportação usa `partitionBy("ano", "mes")` e `compression` `snappy`. A pasta do mês leva o número sem zero à esquerda (`mes=10`; janeiro seria `mes=1`). O rodapé do arquivo exportado mostra `SNAPPY` em todas as colunas.
- **Reprocessamento:** todas as tabelas são recriadas inteiras (`CREATE OR REPLACE TABLE`) e a exportação usa `overwrite`, então reexecutar o mesmo período não duplica dados. A extração apaga os JSON antigos de `raw/usgs` e `raw/open_meteo` só depois que a USGS responde, para não misturar períodos e não perder dados se a rede falhar.

## 12. Saída
- `output/dataset/ano=2026/mes=10/*.snappy.parquet`: 5.376 linhas, 20 colunas no arquivo (`ano` e `mes` ficam no nome das pastas).
- `output/reports/quality_report.json`: relatório da mesma execução (15 de 15 regras aprovadas).

Os arquivos de controle que o Databricks grava junto (`_SUCCESS`, `_committed_*`, `_started_*`) não são versionados.

## 13. Limitações conhecidas
- **Open-Meteo:** plano gratuito só para uso não comercial; dados ERA5 com atraso de 5 dias, então dias muito recentes podem não ter clima.
- **USGS:** limite de taxa não publicado; o projeto usa 1 s entre chamadas como valor conservador (A7). Mais de 20.000 eventos no período faz a extração parar com erro, sem paginação. O fim do período é enviado como só data (`endtime` do dia seguinte); o horário exato desse limite é **A validar** (A9).
- **Catálogo:** o nome `ft03_sismos_clima` está escrito nos SQL; o parâmetro `catalogo` só vale para os notebooks Python (DT-05).
- **Regra Q-06:** usa magnitude mínima 5 fixa; rodar com outra `magnitude_minima` reprova a regra (DT-07).
- **`gold.qualidade_regras`:** não guarda o horário de geração (DT-08).
- **`run.sh`:** confere o `result_state` da execução, porque o `databricks` instalado pelo pip (0.18), que redireciona para a CLI nova, devolveu 0 numa falha (OB-47).
- **Bibliotecas no serverless:** o `requests` usado no workspace é o do ambiente; a versão dele não foi conferida contra o `requirements.txt` (A validar).
- **Free Edition:** uso pessoal, serverless, cotas não publicadas em número.
- **Período testado:** só outubro de 2026.

## 14. Licenças dos dados
- USGS: dado do governo dos EUA (domínio público), **A validar** na página de política da USGS.
- Open-Meteo: CC BY 4.0, atribuição obrigatória; plano gratuito só para uso não comercial.

## 15. Documentação
O portal do projeto (`portal/index.html`, abre offline) reúne os documentos, o progresso e a apresentação técnica; regerar com `python portal/gerar_portal.py`. `docs/` tem requisitos com evidência (`01-negocio/requisitos.md`), estado do projeto, decisões, débito técnico e observações datadas de cada teste (`00-gestao/`), plano e arquitetura (`02-arquitetura/`) e fontes (`03-tecnico/`). Regra do projeto: nada inferido; o que não está em documentação oficial ou em teste real fica **A validar**.

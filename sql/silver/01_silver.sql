-- Databricks notebook source
-- DBTITLE 1,Resumo do arquivo
-- MAGIC %md
-- MAGIC # 01_silver (SQL)
-- MAGIC **O que faz:** cria a camada silver: desaninha as listas da bronze e aplica as transformações T1 (tipos e datas), T2 (nulos) e T3 (deduplicação). Tarefa `silver` do job.
-- MAGIC
-- MAGIC **O que contém:**
-- MAGIC - `silver.sismos`: 12 colunas, 1 linha por sismo (`explode(features)`; deduplicação por `evento_id` com `QUALIFY row_number()`, mantendo a versão de `atualizado_em` mais recente)
-- MAGIC - `silver.clima_horario`: 10 colunas, 1 linha por sismo e hora (`posexplode(hourly.time)` guarda a posição para ler as listas paralelas)
-- MAGIC - conferências de contagem e de nulos no fim
-- MAGIC
-- MAGIC **Resultado esperado:** `silver.sismos` com 1 linha por sismo da USGS e `silver.clima_horario` com 24 linhas por sismo. Linha sem chave, instante, magnitude ou coordenada é rejeitada; clima nulo continua nulo. Tabelas recriadas inteiras.

-- COMMAND ----------

-- DBTITLE 1,Fixar fuso UTC
SET TIME ZONE 'UTC';  -- datas e horas desta sessão passam a ser calculadas e exibidas em UTC
SELECT current_timezone() AS fuso;  -- confirma o fuso da sessão (esperado: UTC)

-- COMMAND ----------

-- DBTITLE 1,Criar silver.sismos
-- Silver dos sismos: desaninha a lista features e aplica T1 (tipos), T2 (nulos) e T3 (deduplicação)
CREATE OR REPLACE TABLE ft03_sismos_clima.silver.sismos AS  -- recria a tabela inteira: reexecutar não duplica
WITH desaninhado AS (  -- passo 1: uma linha por sismo
  SELECT
    explode(features) AS f,  -- cada item da lista features vira uma linha
    _arquivo  -- arquivo de origem, herdado da bronze
  FROM ft03_sismos_clima.bronze.usgs_resposta
),
tipado AS (  -- passo 2 (T1): nomes finais e tipos corretos
  SELECT
    f.id AS evento_id,  -- chave do sismo
    CAST(f.properties.mag AS DOUBLE) AS magnitude,  -- magnitude
    f.properties.magType AS tipo_magnitude,  -- tipo da magnitude (ex.: mww, mb)
    coalesce(f.properties.place, 'Não informado') AS `local`,  -- T2: local nulo vira texto fixo, sem inventar valor
    timestamp_millis(f.properties.time) AS instante_utc,  -- T1: milissegundos viram TIMESTAMP
    CAST(timestamp_millis(f.properties.time) AS DATE) AS data_utc,  -- dia UTC do sismo (decisão P-03)
    CAST(try_element_at(f.geometry.coordinates, 1) AS DOUBLE) AS longitude,  -- 1º item da lista; NULL se a lista for curta
    CAST(try_element_at(f.geometry.coordinates, 2) AS DOUBLE) AS latitude,  -- 2º item da lista
    CAST(try_element_at(f.geometry.coordinates, 3) AS DOUBLE) AS profundidade_km,  -- 3º item da lista
    f.properties.status AS status_revisao,  -- reviewed ou automatic
    timestamp_millis(f.properties.updated) AS atualizado_em,  -- última atualização do evento
    _arquivo AS arquivo_origem  -- rastreio até o arquivo bruto
  FROM desaninhado
)
SELECT *
FROM tipado
WHERE evento_id IS NOT NULL  -- T2: sem chave, a linha é rejeitada
  AND magnitude IS NOT NULL  -- T2: sem magnitude, rejeitada
  AND instante_utc IS NOT NULL  -- T2: sem instante, rejeitada
  AND longitude IS NOT NULL  -- T2: sem coordenada, rejeitada
  AND latitude IS NOT NULL  -- T2: sem coordenada, rejeitada
QUALIFY row_number() OVER (PARTITION BY evento_id ORDER BY atualizado_em DESC) = 1;  -- T3: por evento, fica a versão mais recente

-- COMMAND ----------

-- DBTITLE 1,Conferir silver.sismos
SELECT
  count(*) AS linhas,  -- sismos na silver
  count(DISTINCT evento_id) AS ids_distintos,  -- deve ser igual a linhas
  min(data_utc) AS primeiro_dia,  -- primeiro dia UTC
  max(data_utc) AS ultimo_dia,  -- último dia UTC
  min(magnitude) AS mag_min,  -- menor magnitude
  max(magnitude) AS mag_max  -- maior magnitude
FROM ft03_sismos_clima.silver.sismos;

-- COMMAND ----------

-- DBTITLE 1,Ver primeiros sismos da silver
SELECT evento_id, magnitude, instante_utc, data_utc, longitude, latitude, profundidade_km, `local`  -- campos principais
FROM ft03_sismos_clima.silver.sismos
ORDER BY instante_utc  -- do mais antigo para o mais recente
LIMIT 3;

-- COMMAND ----------

-- DBTITLE 1,Ver tipos da silver.sismos
DESCRIBE TABLE ft03_sismos_clima.silver.sismos;  -- nomes e tipos das colunas

-- COMMAND ----------

-- DBTITLE 1,Criar silver.clima_horario
-- Silver do clima: 1 linha por sismo e hora. Aplica T1 (tipos), T2 (nulos) e T3 (deduplicação)
CREATE OR REPLACE TABLE ft03_sismos_clima.silver.clima_horario AS  -- recria a tabela inteira: reexecutar não duplica
WITH horas AS (  -- passo 1: uma linha por sismo e hora
  SELECT
    regexp_extract(_arquivo, '([^/]+)\\.json$', 1) AS evento_id,  -- a resposta não traz o id: ele vem do nome do arquivo
    try_cast(hora AS TIMESTAMP) AS hora_utc,  -- T1: texto ISO vira TIMESTAMP; NULL se o texto for inválido (sessão em UTC)
    CAST(try_element_at(hourly.temperature_2m, pos + 1) AS DOUBLE) AS temperatura_c,  -- mesma posição da hora (pos começa em 0, a lista em 1)
    CAST(try_element_at(hourly.relative_humidity_2m, pos + 1) AS DOUBLE) AS umidade_pct,  -- T1: vem como inteiro, vira DOUBLE
    CAST(try_element_at(hourly.precipitation, pos + 1) AS DOUBLE) AS precipitacao_mm,  -- precipitação em mm
    CAST(try_element_at(hourly.wind_speed_10m, pos + 1) AS DOUBLE) AS vento_kmh,  -- vento em km/h
    CAST(try_element_at(hourly.surface_pressure, pos + 1) AS DOUBLE) AS pressao_hpa,  -- pressão em hPa
    CAST(latitude AS DOUBLE) AS latitude_grade,  -- latitude do ponto de grade usado pelo Open-Meteo
    CAST(longitude AS DOUBLE) AS longitude_grade,  -- longitude do ponto de grade
    CAST(elevation AS DOUBLE) AS elevacao_m,  -- elevação do ponto de grade, em metros
    _lido_em  -- usado só para desempatar duplicatas
  FROM ft03_sismos_clima.bronze.meteo_resposta
  LATERAL VIEW posexplode(hourly.time) h AS pos, hora  -- uma linha por item de time, com a posição
)
SELECT
  evento_id, hora_utc, temperatura_c, umidade_pct, precipitacao_mm, vento_kmh, pressao_hpa,  -- T2: variável climática nula continua nula, sem preencher
  latitude_grade, longitude_grade, elevacao_m
FROM horas
WHERE evento_id <> ''  -- T2: sem id (o regexp devolve texto vazio quando não casa), a linha é rejeitada
  AND hora_utc IS NOT NULL  -- T2: sem instante válido, rejeitada
QUALIFY row_number() OVER (PARTITION BY evento_id, hora_utc ORDER BY _lido_em DESC) = 1;  -- T3: por sismo e hora, fica a leitura mais recente

-- COMMAND ----------

-- DBTITLE 1,Conferir silver.clima_horario
SELECT
  count(*) AS linhas,  -- esperado: sismos x 24
  count(DISTINCT evento_id) AS sismos,  -- esperado: 1 por sismo da USGS
  min(hora_utc) AS primeira_hora,  -- primeira hora
  max(hora_utc) AS ultima_hora,  -- última hora
  count_if(temperatura_c IS NULL) AS sem_temperatura,  -- nulos de temperatura
  min(temperatura_c) AS temp_min,  -- menor temperatura
  max(temperatura_c) AS temp_max  -- maior temperatura
FROM ft03_sismos_clima.silver.clima_horario;

-- COMMAND ----------

-- DBTITLE 1,Conferir horas por sismo e cruzamento
SELECT
  (SELECT min(horas) FROM (SELECT count(*) AS horas FROM ft03_sismos_clima.silver.clima_horario GROUP BY evento_id)) AS horas_min_por_sismo,  -- menor quantidade de horas de um sismo
  (SELECT max(horas) FROM (SELECT count(*) AS horas FROM ft03_sismos_clima.silver.clima_horario GROUP BY evento_id)) AS horas_max_por_sismo,  -- maior quantidade de horas de um sismo
  (SELECT count(*) FROM ft03_sismos_clima.silver.sismos s  -- sismos sem nenhuma hora de clima
     WHERE NOT EXISTS (SELECT 1 FROM ft03_sismos_clima.silver.clima_horario c WHERE c.evento_id = s.evento_id)) AS sismos_sem_clima,
  (SELECT count(*) FROM (SELECT DISTINCT evento_id FROM ft03_sismos_clima.silver.clima_horario) c  -- clima sem sismo correspondente
     WHERE NOT EXISTS (SELECT 1 FROM ft03_sismos_clima.silver.sismos s WHERE s.evento_id = c.evento_id)) AS clima_sem_sismo;

-- COMMAND ----------

-- DBTITLE 1,Ver tipos da silver.clima_horario
DESCRIBE TABLE ft03_sismos_clima.silver.clima_horario;  -- nomes e tipos das colunas
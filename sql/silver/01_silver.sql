-- Databricks notebook source
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

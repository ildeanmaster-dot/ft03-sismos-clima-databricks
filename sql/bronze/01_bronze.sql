-- Databricks notebook source
-- DBTITLE 1,Criar bronze.usgs_resposta
-- Bronze da USGS: 1 linha por arquivo de resposta, exatamente como a API devolveu
CREATE OR REPLACE TABLE ft03_sismos_clima.bronze.usgs_resposta AS  -- recria a tabela inteira: reexecutar não duplica linhas
SELECT
  *,  -- colunas do JSON como vieram: type, metadata, features, bbox e _rescued_data
  _metadata.file_path AS _arquivo,  -- caminho do arquivo de origem, para rastrear cada linha
  current_timestamp() AS _lido_em  -- instante em que o arquivo foi lido
FROM read_files(  -- lê a pasta de JSON como tabela
  '/Volumes/ft03_sismos_clima/bronze/raw/usgs/',  -- pasta gravada pela extração
  format => 'json'  -- formato dos arquivos
);

-- COMMAND ----------

-- DBTITLE 1,Criar bronze.meteo_resposta
-- Bronze do Open-Meteo: 1 linha por sismo (um arquivo por sismo), sem tratamento
CREATE OR REPLACE TABLE ft03_sismos_clima.bronze.meteo_resposta AS  -- recria a tabela inteira a cada execução
SELECT
  *,  -- colunas do JSON como vieram: latitude, longitude, elevation, hourly, hourly_units e demais
  _metadata.file_path AS _arquivo,  -- o nome do arquivo carrega o evento_id (a resposta não traz o id)
  current_timestamp() AS _lido_em  -- instante em que o arquivo foi lido
FROM read_files(  -- lê a pasta de JSON como tabela
  '/Volumes/ft03_sismos_clima/bronze/raw/open_meteo/',  -- pasta gravada pela extração
  format => 'json'  -- formato dos arquivos
);

-- COMMAND ----------

-- DBTITLE 1,Conferir contagens da bronze
SELECT 'usgs_resposta' AS tabela, count(*) AS linhas, sum(size(features)) AS itens_internos  -- 1 arquivo, N sismos
FROM ft03_sismos_clima.bronze.usgs_resposta
UNION ALL  -- junta os dois resultados mantendo todas as linhas
SELECT 'meteo_resposta', count(*), sum(size(hourly.time))  -- 1 arquivo por sismo, 24 horas cada
FROM ft03_sismos_clima.bronze.meteo_resposta;

-- COMMAND ----------

-- DBTITLE 1,Ver caminho do arquivo de origem
SELECT _arquivo, _lido_em  -- origem e instante de leitura de 3 linhas
FROM ft03_sismos_clima.bronze.meteo_resposta
ORDER BY _arquivo  -- ordem estável
LIMIT 3;

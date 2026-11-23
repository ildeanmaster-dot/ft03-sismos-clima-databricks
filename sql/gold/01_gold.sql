-- Databricks notebook source
-- DBTITLE 1,Fixar fuso UTC
SET TIME ZONE 'UTC';  -- datas e horas desta sessão passam a ser calculadas e exibidas em UTC
SELECT current_timezone() AS fuso;  -- confirma o fuso da sessão (esperado: UTC)

-- COMMAND ----------

-- DBTITLE 1,Prévia do JOIN (T4)
-- T4: cruza cada sismo com as 24 horas de clima do mesmo evento_id. Ainda não cria tabela, só mostra o resultado
SELECT
  s.evento_id,  -- chave do cruzamento, presente nas duas tabelas
  s.magnitude,  -- vem de silver.sismos
  s.instante_utc,  -- instante exato do sismo
  c.hora_utc,  -- vem de silver.clima_horario: uma hora do dia do sismo
  c.temperatura_c  -- temperatura daquela hora
FROM ft03_sismos_clima.silver.sismos AS s  -- lado esquerdo: 1 linha por sismo
INNER JOIN ft03_sismos_clima.silver.clima_horario AS c  -- lado direito: 24 linhas por sismo
  ON c.evento_id = s.evento_id  -- só junta linhas com o mesmo evento_id
ORDER BY s.evento_id, c.hora_utc  -- ordem estável para conferir
LIMIT 5;  -- só as 5 primeiras linhas

-- COMMAND ----------

-- DBTITLE 1,Conferir o JOIN (sem multiplicar linhas)
-- Compara o resultado do JOIN com o que se espera: 224 sismos x 24 horas = 5376
SELECT
  (SELECT count(*)  -- JOIN interno: só linhas que existem nos dois lados
     FROM ft03_sismos_clima.silver.sismos AS s
     INNER JOIN ft03_sismos_clima.silver.clima_horario AS c ON c.evento_id = s.evento_id) AS linhas_inner,
  (SELECT count(*)  -- JOIN à esquerda: mantém também sismo sem clima (com hora nula)
     FROM ft03_sismos_clima.silver.sismos AS s
     LEFT JOIN ft03_sismos_clima.silver.clima_horario AS c ON c.evento_id = s.evento_id) AS linhas_left,
  (SELECT count(*) FROM ft03_sismos_clima.silver.clima_horario) AS linhas_clima,  -- tamanho da tabela de clima
  (SELECT count(*) * 24 FROM ft03_sismos_clima.silver.sismos) AS esperado  -- 224 sismos x 24 horas

-- COMMAND ----------

-- DBTITLE 1,Criar gold.sismo_clima_horario
-- Gold: T4 (JOIN) + T5 (métricas). 1 linha por sismo e hora, particionada por ano e mês, com compressão Snappy
CREATE OR REPLACE TABLE ft03_sismos_clima.gold.sismo_clima_horario  -- recria a tabela inteira: reexecutar não duplica
PARTITIONED BY (ano, mes)  -- os dados ficam em pastas separadas por ano e mês (colunas calculadas abaixo)
TBLPROPERTIES ('delta.parquet.compression.codec' = 'SNAPPY')  -- pede compressão Snappy nos arquivos Parquet desta tabela
AS
WITH juncao AS (  -- passo 1 (T4): cruza cada sismo com suas 24 horas de clima
  SELECT
    s.evento_id,  -- chave do cruzamento
    s.`local`,  -- descrição do lugar (crases porque local é palavra reservada)
    s.data_utc,  -- dia UTC do sismo, usado para ano e mês
    s.instante_utc AS instante_sismo_utc,  -- instante exato do sismo, com nome claro na gold
    s.magnitude, s.latitude, s.longitude, s.profundidade_km,  -- dados do sismo, repetidos nas 24 linhas
    c.hora_utc,  -- hora do clima
    c.temperatura_c, c.umidade_pct, c.precipitacao_mm, c.vento_kmh, c.pressao_hpa  -- as 5 variáveis climáticas
  FROM ft03_sismos_clima.silver.sismos AS s  -- 1 linha por sismo
  INNER JOIN ft03_sismos_clima.silver.clima_horario AS c  -- 24 linhas por sismo
    ON c.evento_id = s.evento_id  -- junta pelo mesmo evento_id
),
horas AS (  -- passo 2 (T5): distância de cada hora até a hora do sismo
  SELECT
    *,  -- mantém todas as colunas do passo 1
    CAST(timestampdiff(HOUR, date_trunc('hour', instante_sismo_utc), hora_utc) AS INT) AS horas_desde_sismo  -- hora do clima menos a hora cheia do sismo; negativo = antes
  FROM juncao
)
SELECT  -- passo 3 (T5): colunas finais, faixa, período e métricas do dia
  evento_id, `local`,  -- identificação e lugar
  year(data_utc) AS ano,  -- ano do sismo (INT), usado na partição
  month(data_utc) AS mes,  -- mês do sismo (INT), usado na partição
  data_utc, instante_sismo_utc, magnitude, latitude, longitude, profundidade_km,  -- dados do sismo
  hora_utc, temperatura_c, umidade_pct, precipitacao_mm, vento_kmh, pressao_hpa,  -- dados do clima
  CASE  -- faixa de magnitude: só intervalos numéricos, sem nome de classe
    WHEN magnitude >= 7 THEN '7.0 ou mais'
    WHEN magnitude >= 6 THEN '6.0 a 6.9'
    WHEN magnitude >= 5 THEN '5.0 a 5.9'
    ELSE 'abaixo de 5.0'  -- só aparece se a magnitude mínima do parâmetro for menor que 5
  END AS faixa_magnitude,
  horas_desde_sismo,  -- calculada no passo 2
  CASE  -- período da hora em relação ao sismo
    WHEN horas_desde_sismo < 0 THEN 'antes'
    WHEN horas_desde_sismo = 0 THEN 'hora do sismo'
    ELSE 'depois'
  END AS periodo,
  avg(temperatura_c) OVER (PARTITION BY evento_id) AS temp_media_dia_c,  -- média das 24 horas do sismo (nulos são ignorados)
  max(temperatura_c) OVER (PARTITION BY evento_id) - min(temperatura_c) OVER (PARTITION BY evento_id) AS amplitude_termica_dia_c,  -- maior menos menor temperatura do dia
  sum(precipitacao_mm) OVER (PARTITION BY evento_id) AS precipitacao_total_dia_mm  -- chuva total das 24 horas
FROM horas;

-- COMMAND ----------

-- DBTITLE 1,Conferir gold.sismo_clima_horario
SELECT
  count(*) AS linhas,  -- esperado 5376
  count(DISTINCT evento_id) AS sismos,  -- esperado 224
  count(DISTINCT evento_id, hora_utc) AS pares_unicos,  -- esperado 5376 (nenhum par repetido)
  count_if(periodo = 'hora do sismo') AS horas_do_sismo,  -- esperado 224 (uma por sismo)
  count_if(horas_desde_sismo IS NULL) AS sem_horas_desde,  -- esperado 0
  min(horas_desde_sismo) AS horas_desde_min,  -- esperado entre -23 e 0
  max(horas_desde_sismo) AS horas_desde_max,  -- esperado entre 0 e 23
  count(DISTINCT faixa_magnitude) AS faixas,  -- esperado 3 (magnitude de 5 a 7,7)
  min(ano) AS ano_min, max(ano) AS ano_max,  -- esperado 2026 e 2026
  min(mes) AS mes_min, max(mes) AS mes_max  -- esperado 10 e 10
FROM ft03_sismos_clima.gold.sismo_clima_horario;

-- COMMAND ----------

-- DBTITLE 1,Ver a virada antes e depois do sismo
-- Um sismo, só as horas ao redor do sismo: mostra horas_desde_sismo e periodo mudando
SELECT evento_id, instante_sismo_utc, hora_utc, horas_desde_sismo, periodo, temperatura_c, temp_media_dia_c, amplitude_termica_dia_c, precipitacao_total_dia_mm
FROM ft03_sismos_clima.gold.sismo_clima_horario
WHERE evento_id = 'aka2026tuxgky'  -- o mesmo sismo da prévia do JOIN
  AND horas_desde_sismo BETWEEN -1 AND 1  -- uma hora antes, a hora do sismo e uma hora depois
ORDER BY hora_utc;

-- COMMAND ----------

-- DBTITLE 1,Ver propriedades da gold (A3)
SHOW TBLPROPERTIES ft03_sismos_clima.gold.sismo_clima_horario;  -- lista as propriedades gravadas, para ver se o Snappy ficou registrado

-- COMMAND ----------

-- DBTITLE 1,Ver partições da gold
DESCRIBE DETAIL ft03_sismos_clima.gold.sismo_clima_horario;  -- mostra partitionColumns, numFiles e sizeInBytes
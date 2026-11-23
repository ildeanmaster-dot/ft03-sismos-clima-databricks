-- Databricks notebook source
-- DBTITLE 1,Fixar fuso UTC
SET TIME ZONE 'UTC';  -- a regra Q-12 converte hora em data, e essa conversão depende do fuso da sessão
SELECT current_timezone() AS fuso;  -- confirma o fuso da sessão (esperado: UTC)

-- COMMAND ----------

-- DBTITLE 1,Criar gold.qualidade_regras
-- Cada linha é uma regra: quantos registros foram verificados e quantos violam. Violações = 0 significa aprovada
CREATE OR REPLACE TABLE ft03_sismos_clima.gold.qualidade_regras AS  -- recria a tabela inteira a cada execução
SELECT *,  -- todas as colunas da regra
  CASE WHEN violacoes = 0 THEN 'aprovada' ELSE 'reprovada' END AS status  -- decisão da regra
FROM (
  SELECT 'Q-02' AS regra_id, 'Sem nulos em evento_id, instante_utc, magnitude, latitude e longitude (silver.sismos)' AS descricao,
    'null ratio' AS tipo, 'erro' AS nivel,
    count(*) AS verificados,  -- sismos verificados
    count_if(evento_id IS NULL OR instante_utc IS NULL OR magnitude IS NULL OR latitude IS NULL OR longitude IS NULL) AS violacoes  -- linhas com algum campo nulo
  FROM ft03_sismos_clima.silver.sismos
  UNION ALL
  SELECT 'Q-04', 'evento_id único em silver.sismos', 'unicidade', 'erro',
    count(*),  -- sismos verificados
    count(*) - count(DISTINCT evento_id)  -- linhas a mais que ids distintos = repetidas
  FROM ft03_sismos_clima.silver.sismos
  UNION ALL
  SELECT 'Q-05a', '(evento_id, hora_utc) único em silver.clima_horario', 'unicidade', 'erro',
    count(*),  -- horas de clima verificadas
    count(*) - count(DISTINCT evento_id, hora_utc)  -- pares repetidos
  FROM ft03_sismos_clima.silver.clima_horario
  UNION ALL
  SELECT 'Q-05b', '(evento_id, hora_utc) único em gold.sismo_clima_horario', 'unicidade', 'erro',
    count(*),  -- linhas da gold verificadas
    count(*) - count(DISTINCT evento_id, hora_utc)  -- pares repetidos
  FROM ft03_sismos_clima.gold.sismo_clima_horario
  UNION ALL
  SELECT 'Q-06', 'magnitude maior ou igual a 5 (silver.sismos)', 'intervalo', 'erro',
    count(*),  -- sismos verificados
    count_if(magnitude < 5)  -- sismos abaixo do mínimo
  FROM ft03_sismos_clima.silver.sismos
  UNION ALL
  SELECT 'Q-07', 'Latitude entre -90 e 90 e longitude entre -180 e 180 (silver.sismos)', 'intervalo', 'erro',
    count(*),  -- sismos verificados
    count_if(latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180)  -- coordenadas fora do mapa (nulos não entram aqui, a Q-02 cuida deles)
  FROM ft03_sismos_clima.silver.sismos
  UNION ALL
  SELECT 'Q-08', 'Umidade entre 0 e 100 e precipitação maior ou igual a 0 (silver.clima_horario)', 'intervalo', 'erro',
    count(*),  -- horas de clima verificadas
    count_if(umidade_pct NOT BETWEEN 0 AND 100 OR precipitacao_mm < 0)  -- valores impossíveis
  FROM ft03_sismos_clima.silver.clima_horario
  UNION ALL
  SELECT 'Q-09', '24 horas por sismo (gold)', 'completude', 'erro',
    (SELECT count(DISTINCT evento_id) FROM ft03_sismos_clima.gold.sismo_clima_horario),  -- sismos verificados
    (SELECT count(*) FROM (SELECT evento_id FROM ft03_sismos_clima.gold.sismo_clima_horario GROUP BY evento_id HAVING count(*) <> 24))  -- sismos com quantidade de horas diferente de 24
  UNION ALL
  SELECT 'Q-11', 'Linhas da gold = sismos x 24 e nenhum sismo sem clima', 'JOIN', 'erro',
    (SELECT count(*) FROM ft03_sismos_clima.gold.sismo_clima_horario),  -- linhas da gold verificadas
    abs((SELECT count(*) FROM ft03_sismos_clima.gold.sismo_clima_horario) - 24 * (SELECT count(*) FROM ft03_sismos_clima.silver.sismos))  -- diferença entre o real e o esperado
      + (SELECT count(*) FROM ft03_sismos_clima.silver.sismos AS s
           WHERE NOT EXISTS (SELECT 1 FROM ft03_sismos_clima.gold.sismo_clima_horario AS g WHERE g.evento_id = s.evento_id))  -- sismos que não chegaram à gold
  UNION ALL
  SELECT 'Q-12', 'Dia de hora_utc igual a data_utc do sismo (gold)', 'consistência', 'erro',
    count(*),  -- linhas da gold verificadas
    count_if(CAST(hora_utc AS DATE) <> data_utc)  -- hora que cai em outro dia
  FROM ft03_sismos_clima.gold.sismo_clima_horario
);

-- COMMAND ----------

-- DBTITLE 1,Conferir gold.qualidade_regras
SELECT regra_id, descricao, nivel, verificados, violacoes, status  -- resultado de cada regra
FROM ft03_sismos_clima.gold.qualidade_regras
ORDER BY regra_id;  -- ordem das regras
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

-- COMMAND ----------

-- DBTITLE 1,Testar as regras com dados ruins
-- Teste negativo: aplica a mesma expressão de cada regra a poucas linhas inventadas, com defeito de propósito
-- Se a regra detecta, 'encontradas' é igual a 'esperadas'. Isto testa a expressão, não as tabelas reais
SELECT regra_id, encontradas, esperadas,  -- quanto a regra achou e quanto devia achar
  CASE WHEN encontradas = esperadas THEN 'detectou' ELSE 'falhou' END AS resultado  -- a regra funciona se os dois batem
FROM (
  SELECT 'Q-02' AS regra_id,
    count_if(evento_id IS NULL OR magnitude IS NULL) AS encontradas,  -- mesma ideia da Q-02: algum campo nulo
    2 AS esperadas  -- 2 linhas têm nulo
  FROM VALUES ('x', 1.0), (CAST(NULL AS STRING), 2.0), ('y', CAST(NULL AS DOUBLE)) AS t(evento_id, magnitude)
  UNION ALL
  SELECT 'Q-04', count(*) - count(DISTINCT evento_id), 1  -- 3 linhas e 2 ids distintos: 1 repetida
  FROM VALUES ('a'), ('a'), ('b') AS t(evento_id)
  UNION ALL
  SELECT 'Q-06', count_if(magnitude < 5), 2  -- 4.9 e 3.0 estão abaixo de 5
  FROM VALUES (4.9), (5.0), (3.0) AS t(magnitude)
  UNION ALL
  SELECT 'Q-07', count_if(latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180), 2  -- latitude 91 e longitude 181
  FROM VALUES (91.0, 0.0), (0.0, 181.0), (10.0, 20.0) AS t(latitude, longitude)
  UNION ALL
  SELECT 'Q-08', count_if(umidade_pct NOT BETWEEN 0 AND 100 OR precipitacao_mm < 0), 2  -- umidade 101 e chuva -1
  FROM VALUES (101.0, 0.0), (50.0, -1.0), (50.0, 0.0) AS t(umidade_pct, precipitacao_mm)
  UNION ALL
  SELECT 'Q-12', count_if(CAST(hora_utc AS DATE) <> data_utc), 1  -- a segunda hora já é do dia 02
  FROM VALUES (TIMESTAMP'2026-10-01 23:00:00', DATE'2026-10-01'), (TIMESTAMP'2026-10-02 00:00:00', DATE'2026-10-01') AS t(hora_utc, data_utc)
)
ORDER BY regra_id;  -- ordem das regras

-- COMMAND ----------

-- DBTITLE 1,Testar Q-05a, Q-05b, Q-09 e Q-11 com dados ruins
-- Teste negativo das 4 regras que faltavam (OB-31): mesma expressão de cada regra sobre tabelas inventadas com defeito
-- Se 'encontradas' for igual a 'esperadas', a regra detecta o defeito. Isto testa a expressão, não as tabelas reais
WITH clima_teste AS (  -- Q-05a: 4 horas de clima, com o par (a, 00:00) repetido
  SELECT * FROM VALUES ('a', TIMESTAMP'2026-10-01 00:00:00'), ('a', TIMESTAMP'2026-10-01 00:00:00'), ('a', TIMESTAMP'2026-10-01 01:00:00'), ('b', TIMESTAMP'2026-10-01 00:00:00') AS t(evento_id, hora_utc)  -- linhas inventadas
),
gold_pares_teste AS (  -- Q-05b: a hora 10:00 do sismo c aparece 3 vezes (2 linhas a mais)
  SELECT * FROM VALUES ('c', TIMESTAMP'2026-10-01 10:00:00'), ('c', TIMESTAMP'2026-10-01 10:00:00'), ('c', TIMESTAMP'2026-10-01 10:00:00'), ('d', TIMESTAMP'2026-10-01 10:00:00') AS t(evento_id, hora_utc)  -- linhas inventadas
),
gold_horas_teste AS (  -- Q-09 e Q-11: sismo a com 24 horas, b com 23 e c com 25
  SELECT 'a' AS evento_id, explode(sequence(0, 23)) AS hora  -- 24 linhas para o sismo a
  UNION ALL SELECT 'b', explode(sequence(0, 22))  -- 23 linhas para o sismo b (falta 1 hora)
  UNION ALL SELECT 'c', explode(sequence(0, 24))  -- 25 linhas para o sismo c (sobra 1 hora)
),
silver_teste AS (  -- Q-11: 4 sismos na silver; o d não chegou à gold
  SELECT * FROM VALUES ('a'), ('b'), ('c'), ('d') AS t(evento_id)  -- sismos inventados
)
SELECT regra_id, encontradas, esperadas,  -- quanto a regra achou e quanto devia achar
  CASE WHEN encontradas = esperadas THEN 'detectou' ELSE 'falhou' END AS resultado  -- a regra funciona se os dois batem
FROM (
  SELECT 'Q-05a' AS regra_id, count(*) - count(DISTINCT evento_id, hora_utc) AS encontradas, 1 AS esperadas  -- 4 linhas, 3 pares distintos: 1 repetido
  FROM clima_teste
  UNION ALL
  SELECT 'Q-05b', count(*) - count(DISTINCT evento_id, hora_utc), 2  -- 4 linhas, 2 pares distintos: 2 repetidos
  FROM gold_pares_teste
  UNION ALL
  SELECT 'Q-09', count(*), 2  -- b (23 horas) e c (25 horas) têm quantidade diferente de 24
  FROM (SELECT evento_id FROM gold_horas_teste GROUP BY evento_id HAVING count(*) <> 24)  -- sismos com horas faltando ou sobrando
  UNION ALL
  SELECT 'Q-11',
    abs((SELECT count(*) FROM gold_horas_teste) - 24 * (SELECT count(*) FROM silver_teste))  -- |72 - 24 x 4| = 24 linhas de diferença
      + (SELECT count(*) FROM silver_teste AS s WHERE NOT EXISTS (SELECT 1 FROM gold_horas_teste AS g WHERE g.evento_id = s.evento_id)),  -- + 1 sismo (d) sem clima
    25  -- 24 + 1
)
ORDER BY regra_id;  -- ordem das regras
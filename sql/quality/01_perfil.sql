-- Databricks notebook source
-- DBTITLE 1,Fixar fuso UTC
SET TIME ZONE 'UTC';  -- datas e horas desta sessão passam a ser calculadas e exibidas em UTC
SELECT current_timezone() AS fuso;  -- confirma o fuso da sessão (esperado: UTC)

-- COMMAND ----------

-- DBTITLE 1,Perfil das variáveis climáticas da gold
-- Só olha os dados reais: mínimo, máximo e nulos de cada variável. Ainda não é regra de qualidade
SELECT 'temperatura_c' AS variavel,  -- nome da variável
  count(*) AS linhas,  -- total de linhas da gold
  count_if(temperatura_c IS NULL) AS nulos,  -- quantas vieram nulas
  min(temperatura_c) AS minimo, max(temperatura_c) AS maximo, round(avg(temperatura_c), 2) AS media  -- faixa e média observadas
FROM ft03_sismos_clima.gold.sismo_clima_horario
UNION ALL  -- junta o resultado de cada variável numa só tabela
SELECT 'umidade_pct', count(*), count_if(umidade_pct IS NULL), min(umidade_pct), max(umidade_pct), round(avg(umidade_pct), 2)
FROM ft03_sismos_clima.gold.sismo_clima_horario
UNION ALL
SELECT 'precipitacao_mm', count(*), count_if(precipitacao_mm IS NULL), min(precipitacao_mm), max(precipitacao_mm), round(avg(precipitacao_mm), 2)
FROM ft03_sismos_clima.gold.sismo_clima_horario
UNION ALL
SELECT 'vento_kmh', count(*), count_if(vento_kmh IS NULL), min(vento_kmh), max(vento_kmh), round(avg(vento_kmh), 2)
FROM ft03_sismos_clima.gold.sismo_clima_horario
UNION ALL
SELECT 'pressao_hpa', count(*), count_if(pressao_hpa IS NULL), min(pressao_hpa), max(pressao_hpa), round(avg(pressao_hpa), 2)
FROM ft03_sismos_clima.gold.sismo_clima_horario

-- COMMAND ----------

-- DBTITLE 1,Ver as 5 menores pressões e a elevação
-- A menor pressão (541.9 hPa) chamou atenção: aqui vemos onde ela ocorreu e a elevação do ponto de grade
SELECT
  g.evento_id,  -- sismo da linha
  g.`local`,  -- lugar do sismo
  g.hora_utc,  -- hora do clima
  g.pressao_hpa,  -- pressão na superfície naquela hora
  c.elevacao_m  -- elevação do ponto de grade usada pelo Open-Meteo, em metros
FROM ft03_sismos_clima.gold.sismo_clima_horario AS g  -- tabela final
INNER JOIN ft03_sismos_clima.silver.clima_horario AS c  -- a elevação só existe na silver do clima
  ON c.evento_id = g.evento_id AND c.hora_utc = g.hora_utc  -- mesma linha nas duas tabelas
ORDER BY g.pressao_hpa ASC  -- da menor para a maior pressão
LIMIT 5;  -- só as 5 menores
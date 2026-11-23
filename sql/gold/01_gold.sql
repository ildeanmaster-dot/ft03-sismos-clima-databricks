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
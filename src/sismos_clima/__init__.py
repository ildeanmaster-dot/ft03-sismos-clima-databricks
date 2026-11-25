"""Pipeline FT03 Sismos × Clima (USGS + Open-Meteo) no Databricks (serverless).

O que faz: reúne a lógica Python do pipeline, testável sem cluster.
O que contém: config (parâmetros), http_client (taxa e retentativas), extract (extração para o volume bronze) e quality (regras e relatório).
Resultado esperado: os notebooks importam estes módulos e ficam finos; os 34 testes de `tests/` passam.
"""

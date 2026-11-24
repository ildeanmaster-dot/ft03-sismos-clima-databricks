# Requisitos (do PDF FT03_Engenharia_PRJ01_Python)
Versão 0.2 · 24/11/2026

| ID | Requisito | Prior. | Status | Como esta entrega atende |
|---|---|---|---|---|
| RF-01 | 2 APIs públicas de domínios distintos | Alta | Atendido (24/11/2026) | USGS (sismologia) + Open-Meteo (meteorologia), provedores diferentes; out/2026 extraído no serverless: 224 sismos e 224 climas (OB-19, OB-39) |
| RF-02 | Controle de taxa e retentativas com tratamento de erro | Alta | Atendido (24/11/2026) | `src/sismos_clima/http_client.py`: `LimitadorTaxa` (intervalo mínimo entre chamadas) e `ClienteHttp` (timeout, Retry-After, backoff exponencial com teto, erro permanente sem repetir, esgotamento); 8 testes em `tests/test_http_client.py`; testado no serverless (OB-15, OB-16, OB-45) |
| RF-03 | Credenciais por variável de ambiente, sem chave no Git | Alta | Atendido (24/11/2026) | APIs sem chave; `.env.example` sem valores secretos; Databricks por `databricks auth login` (OAuth); `.env` e `jobs/*.local.json` no `.gitignore`; histórico varrido sem token nem `.env` (OB-45) |
| RF-04 | Python modular com funções limpas e type hints | Alta | Atendido (24/11/2026) | `src/sismos_clima/` (`config`, `http_client`, `extract`, `quality`) com type hints; 34 testes passaram (OB-45) |
| RF-05 | Desaninhamento de arrays/JSON via SQL | Alta | Atendido (24/11/2026) | `sql/silver/01_silver.sql`: `explode(features)` da USGS e `posexplode(hourly.time)` com o índice nos demais arrays do Open-Meteo; silver com 224 sismos e 5.376 horas (OB-20 a OB-25) |
| RF-06 | 5 transformações: tipos e datas, nulos, deduplicação, JOIN, métricas | Alta | Atendido (24/11/2026) | `sql/silver/01_silver.sql` (tipos e datas, nulos, deduplicação) e `sql/gold/01_gold.sql` (JOIN por `evento_id`, métricas); gold com 5.376 linhas (OB-27, OB-28) |
| RF-07 | Validações: schema, null ratio, unicidade, intervalo | Alta | Atendido (24/11/2026) | `sql/quality/02_regras.sql` (10 regras, todas com teste negativo) e `src/sismos_clima/quality.py` (schema Q-01, nulos Q-03, contagem Q-10); 15/15 aprovadas (OB-30 a OB-33, OB-44) |
| RF-08 | Relatório de qualidade JSON ou CSV | Alta | Atendido (24/11/2026) | `output/reports/quality_report.json` da execução 931832972977407: 15/15 regras, `aprovado` verdadeiro (OB-43) |
| RF-09 | Parquet ou Delta com Snappy | Alta | Atendido (24/11/2026) | Delta gold com `SNAPPY` + Parquet exportado com `SNAPPY` em todas as colunas, provado no rodapé (OB-41, OB-43) |
| RF-10 | Particionamento temporal (ano/mês) | Alta | Atendido (24/11/2026) | `PARTITIONED BY (ano, mes)` na gold e `partitionBy("ano", "mes")` no Parquet: `output/dataset/ano=2026/mes=10/` (OB-41) |
| RNF-01 | Repositório público com código em `src/` | Alta | Atendido (24/11/2026) | github.com/ildeanmaster-dot/ft03-sismos-clima-databricks com rótulo Public; código em `src/sismos_clima/` (OB-45) |
| RNF-02 | README com execução, variáveis e APIs | Alta | Atendido (24/11/2026) | `README.md` com objetivo, APIs, arquitetura, ambiente, instalação, variáveis e parâmetros, execução, testes, schema, transformações e qualidade, particionamento e reprocessamento, saída e limitações; falta validar num clone limpo |
| RNF-03 | requirements.txt com versões exatas | Alta | Atendido (24/11/2026) | `requirements.txt` com `==` (requests 2.34.2, urllib3 2.8.0, pytest 9.2.0), usado nos testes locais (OB-45); no serverless o `requests` é o do ambiente, versão não conferida (A validar) |
| RNF-04 | run.sh ou comando único | Alta | Atendido (24/11/2026) | `run.sh` dispara o job e espera o fim; execução 357476527649763 com `SUCCESS` (OB-40) |
| RNF-05 | Dataset final em `output/` (.parquet) | Alta | Atendido (24/11/2026) | `output/dataset/ano=2026/mes=10/part-...snappy.parquet`, 5.376 linhas, copiado com `databricks fs cp -r` (OB-43) |

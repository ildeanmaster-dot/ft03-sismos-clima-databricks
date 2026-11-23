# Requisitos (do PDF FT03_Engenharia_PRJ01_Python)
Versão 0.1 · 23/11/2026

| ID | Requisito | Prior. | Status | Como esta entrega atende |
|---|---|---|---|---|
| RF-01 | 2 APIs públicas de domínios distintos | Alta | Pendente | USGS (sismologia) + Open-Meteo (meteorologia); ver R-01 |
| RF-02 | Controle de taxa e retentativas com tratamento de erro | Alta | Pendente | Cliente HTTP único (`src/sismos_clima/http_client.py`) |
| RF-03 | Credenciais por variável de ambiente, sem chave no Git | Alta | Pendente | `.env.example`; APIs sem chave; Databricks por `databricks auth login` |
| RF-04 | Python modular com funções limpas e type hints | Alta | Esqueleto | `src/sismos_clima/` |
| RF-05 | Desaninhamento de arrays/JSON via SQL | Alta | Pendente | `features[]` da USGS e arrays `hourly` do Open-Meteo em SQL (`explode`/`posexplode`) |
| RF-06 | 5 transformações: tipos e datas, nulos, deduplicação, JOIN, métricas | Alta | Pendente | `sql/silver`, `sql/gold` |
| RF-07 | Validações: schema, null ratio, unicidade, intervalo | Alta | Pendente | `src/sismos_clima/quality.py` |
| RF-08 | Relatório de qualidade JSON ou CSV | Alta | Pendente | `output/reports/` |
| RF-09 | Parquet ou Delta com Snappy | Alta | Pendente | Delta gold com `SNAPPY` + export Parquet Snappy (P-02) |
| RF-10 | Particionamento temporal (ano/mês) | Alta | Pendente | `PARTITIONED BY (ano, mes)` pela data UTC do sismo |
| RNF-01 | Repositório público com código em `src/` | Alta | Parcial | Estrutura criada |
| RNF-02 | README com execução, variáveis e APIs | Alta | Parcial | `README.md` |
| RNF-03 | requirements.txt com versões exatas | Alta | Parcial | `requirements.txt` |
| RNF-04 | run.sh ou comando único | Alta | Esqueleto | `run.sh` (P-04) |
| RNF-05 | Dataset final em `output/` (.parquet) | Alta | Pendente | P-02 |

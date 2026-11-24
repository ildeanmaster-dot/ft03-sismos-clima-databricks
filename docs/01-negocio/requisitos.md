# Requisitos (do PDF FT03_Engenharia_PRJ01_Python)
Versão 0.1 · 23/11/2026

| ID | Requisito | Prior. | Status | Como esta entrega atende |
|---|---|---|---|---|
| RF-01 | 2 APIs públicas de domínios distintos | Alta | Pendente | USGS (sismologia) + Open-Meteo (meteorologia); ver R-01 |
| RF-02 | Controle de taxa e retentativas com tratamento de erro | Alta | Pendente | Cliente HTTP único (`src/sismos_clima/http_client.py`) |
| RF-03 | Credenciais por variável de ambiente, sem chave no Git | Alta | Pendente | `.env.example`; APIs sem chave; Databricks por `databricks auth login` |
| RF-04 | Python modular com funções limpas e type hints | Alta | Esqueleto | `src/sismos_clima/` |
| RF-05 | Desaninhamento de arrays/JSON via SQL | Alta | Pendente | `features[]` da USGS e arrays `hourly` do Open-Meteo em SQL (`explode`/`posexplode`) |
| RF-06 | 5 transformações: tipos e datas, nulos, deduplicação, JOIN, métricas | Alta | Implementado | `sql/silver`, `sql/gold` |
| RF-07 | Validações: schema, null ratio, unicidade, intervalo | Alta | Implementado | `src/sismos_clima/quality.py` |
| RF-08 | Relatório de qualidade JSON ou CSV | Alta | Atendido (24/11/2026) | `output/reports/quality_report.json` da execução 931832972977407: 15/15 regras, `aprovado` verdadeiro (OB-43) |
| RF-09 | Parquet ou Delta com Snappy | Alta | Atendido (24/11/2026) | Delta gold com `SNAPPY` + Parquet exportado com `SNAPPY` em todas as colunas, provado no rodapé (OB-41, OB-43) |
| RF-10 | Particionamento temporal (ano/mês) | Alta | Atendido (24/11/2026) | `PARTITIONED BY (ano, mes)` na gold e `partitionBy("ano", "mes")` no Parquet: `output/dataset/ano=2026/mes=10/` (OB-41) |
| RNF-01 | Repositório público com código em `src/` | Alta | Parcial | Estrutura criada |
| RNF-02 | README com execução, variáveis e APIs | Alta | Parcial | `README.md` |
| RNF-03 | requirements.txt com versões exatas | Alta | Parcial | `requirements.txt` |
| RNF-04 | run.sh ou comando único | Alta | Atendido (24/11/2026) | `run.sh` dispara o job e espera o fim; execução 357476527649763 com `SUCCESS` (OB-40) |
| RNF-05 | Dataset final em `output/` (.parquet) | Alta | Atendido (24/11/2026) | `output/dataset/ano=2026/mes=10/part-...snappy.parquet`, 5.376 linhas, copiado com `databricks fs cp -r` (OB-43) |

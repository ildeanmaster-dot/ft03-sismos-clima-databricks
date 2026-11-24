# output/
- `dataset/ano=AAAA/mes=M/*.snappy.parquet`: camada final exportada da gold pelo notebook `05_exportacao`, Parquet com Snappy (provado no rodapé, OB-41). A pasta do mês usa o número sem zero à esquerda (`mes=10`; janeiro seria `mes=1`).
- `reports/quality_report.json`: relatório de qualidade da execução que gerou o dataset.

Origem: volume `/Volumes/ft03_sismos_clima/gold/export/` (`dataset/` e `reports/`), copiado com `databricks fs cp -r`. Os arquivos de controle do Databricks (`_SUCCESS`, `_committed_*`, `_started_*`) não são versionados (`.gitignore`).

# Changelog

## Em desenvolvimento — 24/11/2026
- Job `ft03-sismos-clima-pipeline` descrito em `jobs/ft03_pipeline.json` (6 tarefas, 4 parâmetros); criado no workspace e executado com sucesso (OB-35, OB-36).
- A5 resolvida: parâmetros do job chegam aos notebooks (OB-38).
- `extract.limpar_raw`: a extração apaga os .json antigos de `raw/usgs` e `raw/open_meteo` antes de gravar (DT-09, D-06); 3 testes novos, 34 no total.
- DT-09 validado no workspace: 226 arquivos antigos removidos e outubro inteiro restaurado, 15/15 regras (OB-39).
- `run.sh` (comando único) dispara o job com `jobs/run_padrao.json` e espera o fim (DT-01, OB-40).
- `notebooks/05_exportacao`: Parquet Snappy particionado por ano/mês em `gold.export/dataset`, com prova no rodapé (OB-41); tarefa `exportacao` no job, 7 tarefas (OB-42).
- `output/`: Parquet Snappy de out/2026 (5.376 linhas) e `quality_report.json` da mesma execução; arquivos de controle do Databricks fora do Git (OB-43).
- Teste negativo de Q-05a, Q-05b, Q-09 e Q-11 em `02_regras`: as 10 regras SQL detectam defeito (OB-44).
- Requisitos revisados com evidência: 15 de 15 atendidos, ressalvas registradas (OB-45); `tests/README.md` e README completo na ordem planejada.
- Esboços `notebooks/02_silver.sql` e `notebooks/03_gold.sql` removidos (DT-06).
- Clone limpo validado: LF do `run.sh`, 34 testes no Windows e comando único com `SUCCESS` (OB-46). E8 concluída.
- `run.sh` confere o `result_state` e sai com 1 se o job não terminar em `SUCCESS`; aceita o corpo do `run-now` como argumento (OB-47).
- Portal do projeto (`portal/`) com a aba Apresentação técnica; regras, decisões, arquitetura e diagramas atualizados para o que foi construído (OB-48).

## 0.1.0 — 23/11/2026
- Estrutura inicial do repositório, documentação base (gestão, negócio, arquitetura, fontes) e célula da Etapa 0 (`notebooks/00_validacao_apis.py`).

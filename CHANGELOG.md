# Changelog

## Em desenvolvimento — 24/11/2026
- Job `ft03-sismos-clima-pipeline` descrito em `jobs/ft03_pipeline.json` (6 tarefas, 4 parâmetros); criado no workspace e executado com sucesso (OB-35, OB-36).
- A5 resolvida: parâmetros do job chegam aos notebooks (OB-38).
- `extract.limpar_raw`: a extração apaga os .json antigos de `raw/usgs` e `raw/open_meteo` antes de gravar (DT-09, D-06); 3 testes novos, 34 no total.

## 0.1.0 — 23/11/2026
- Estrutura inicial do repositório, documentação base (gestão, negócio, arquitetura, fontes) e célula da Etapa 0 (`notebooks/00_validacao_apis.py`).

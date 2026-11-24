# Estado do projeto
Versão 0.3 · 24/11/2026

| Etapa | Situação | O que falta |
|---|---|---|
| E0 Validação das APIs | Concluída (23/11/2026) | 224 eventos M5+ em out/2026; 3 sismos x 24 h de clima, 0 nulos |
| E1 Plano detalhado | Aprovado (23/11/2026) | `docs/02-arquitetura/plano-detalhado.md`; recomendações aceitas para P-01 a P-04, P-07 a P-09 |
| E2 Ambiente (catálogo, schemas, volumes, Git folder) | Concluída | Catálogo, schemas, volumes e Git folder criados; import de `src/` testado (OB-10 a OB-13); próxima: E3 extração |
| E3 Extração para bronze | Concluída | Out/2026 extraído: 224 sismos e 224 climas no volume `raw`, relatório sem falhas (OB-14 a OB-19); próxima: E4 bronze e silver |
| E4 Bronze e silver (desaninhamento SQL) | Concluída | Bronze, `silver.sismos` (224) e `silver.clima_horario` (5.376 = 224 x 24) criadas e conferidas (OB-20 a OB-25); próxima: E5 gold |
| E5 Gold (transformações e JOIN) | Concluída | `gold.sismo_clima_horario` com 5.376 linhas (224 x 24), T4 e T5, partição ano/mês e propriedade Snappy registrada (OB-27, OB-28); próxima: E6 qualidade |
| E6 Qualidade e relatório | Concluída | 15 regras aprovadas e `quality_report.json` gravado no volume `gold.export` (OB-29 a OB-33); teste negativo das 10 regras SQL (OB-31, OB-44) |
| E7 Job e comando único | Concluída (24/11/2026) | Job `ft03-sismos-clima-pipeline` criado (OB-35), execução 1 com 6 tarefas `SUCCESS` (OB-36) A5 resolvida (OB-38) e DT-09 resolvido com outubro inteiro restaurado (execução 3, 15/15 regras, OB-39); `run.sh` executado com `SUCCESS` e código de saída 0 (DT-01, OB-40); commit 4de393e no GitHub |
| E8 Exportação Parquet e README final | Concluída (24/11/2026) | `05_exportacao` gravou e provou o Parquet Snappy particionado no volume (OB-41); tarefa `exportacao` no job e execução 5 com 7 tarefas `SUCCESS` (OB-42); dataset e relatório copiados para `output/` (OB-43); teste negativo das 4 regras restantes (OB-44); requisitos revisados (OB-45); README completo; esboços removidos (DT-06); clone limpo com LF do `run.sh`, 34 testes no Windows e job `SUCCESS` (OB-46) |
| E9 Portal e apresentação | Concluída (24/11/2026) | `portal/index.html` gerado dos documentos, com as abas Apresentação técnica, Roteiro de execução e Execução animada (`docs/04-apresentacao/`); testado no Chromium (OB-48, OB-49); notebook `notebooks/validacao_do_pipeline` validado no workspace (OB-50, OB-51) |

| Componente | Situação | Evidência |
|---|---|---|
| Rede do Free Edition para as 2 APIs | Liberada | teste no workspace, 23/11/2026 (OB-01, OB-06 a OB-09) |
| Catálogo, schemas, volumes e Git folder | Criados | OB-10 a OB-13 |
| Extração resiliente (`config`, `http_client`, `extract`) | Implementado | 224 sismos e 224 climas, 226 chamadas (OB-15 a OB-19, OB-39) |
| Bronze (`sql/bronze/01_bronze`) | Implementado | 1 resposta USGS e 224 respostas de clima (OB-21) |
| Silver com desaninhamento SQL (`sql/silver/01_silver`) | Implementado | 224 sismos e 5.376 horas (OB-22 a OB-25) |
| Gold com JOIN e métricas (`sql/gold/01_gold`) | Implementado | 5.376 linhas, partição ano/mês, Snappy (OB-27, OB-28) |
| Qualidade (`sql/quality/02_regras`, `quality.py`, `04_qualidade`) | Implementado | 15/15 regras aprovadas, 10 regras SQL com teste negativo (OB-30 a OB-33, OB-44) |
| Exportação (`notebooks/05_exportacao`) | Implementado | Parquet Snappy provado no rodapé (OB-41) |
| Job com 7 tarefas e `run.sh` | Implementado | execução 931832972977407 `SUCCESS` em 281 s (OB-42) |
| Testes unitários | Implementado | 34 passed no Linux e no Windows (OB-45, OB-46) |
| `output/` (dataset e relatório) | Versionado | OB-43 |
| README e clone limpo | Validado | OB-46 |
| Notebook de validação (`notebooks/validacao_do_pipeline`) | Validado | 25 células só de leitura, Serverless, sem erro (OB-51) |
| Portal do projeto (`portal/index.html`) | Gerado | 16 rotas e 14 diagramas sem erro (OB-48); regerar com `python portal/gerar_portal.py` |

| # | Ação | Quem |
|---|---|---|
| 1 | Aguardar o aceite da 2ª entrega pela turma (P-05) | Ildean |
| 2 | Débitos abertos: DT-03 (licença), DT-04 (taxa da USGS), DT-05 (catálogo nos SQL), DT-07 (Q-06 fixa), DT-08 (`executado_em`), DT-10 (`raw/_teste`) e DT-11 (rascunhos na Home) | Ildean e Claude |
| 3 | A validar: A7 (taxa da USGS), A9 (`endtime` só com data) e A11 (versão do `requests` no serverless) | Claude, com teste no workspace |
| 4 | Fora deste repositório: levar a leitura de `P-05`/`D-05` do gerador do portal aos portais da Monte Bravo; apagar `D:\Portifolio\clone-limpo-ft03`; e-mail do workspace segue no histórico antigo do Git (OB-13), mantido por decisão do responsável | Ildean e Claude |
| 5 | Novos ensaios da apresentação: `notebooks/validacao_do_pipeline` e o Roteiro de execução (seção 0) | Ildean |

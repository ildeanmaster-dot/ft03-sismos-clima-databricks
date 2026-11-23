# Estado do projeto
Versão 0.1 · 23/11/2026

| Etapa | Situação | O que falta |
|---|---|---|
| E0 Validação das APIs | Concluída (23/11/2026) | 224 eventos M5+ em out/2026; 3 sismos x 24 h de clima, 0 nulos |
| E1 Plano detalhado | Aprovado (23/11/2026) | `docs/02-arquitetura/plano-detalhado.md`; recomendações aceitas para P-01 a P-04, P-07 a P-09 |
| E2 Ambiente (catálogo, schemas, volumes, Git folder) | Concluída | Catálogo, schemas, volumes e Git folder criados; import de `src/` testado (OB-10 a OB-13); próxima: E3 extração |
| E3 Extração para bronze | Em andamento | `config.py`, `http_client.py` (taxa e retentativas) e funções de parâmetros do `extract.py` testados no workspace (OB-14 a OB-17); `extrair` (gravação no volume) escrito, falta testar no workspace |
| E4 Silver (desaninhamento SQL) | Pendente | E3 |
| E5 Gold (transformações e JOIN) | Pendente | E4 |
| E6 Qualidade e relatório | Pendente | E5 |
| E7 Job e comando único | Pendente | E6 |
| E8 Exportação Parquet e README final | Pendente | E7 |

| Componente | Situação | Evidência |
|---|---|---|
| Estrutura do repositório | Criada | este repositório, 23/11/2026 |
| Etapa 0 (4 células) | Executada no workspace | `notebooks/00_validacao_apis.py`, OB-06 a OB-09 |
| Rede do Free Edition para as 2 APIs | Liberada | teste do responsável no workspace, 23/11/2026 |

| # | Ação | Quem |
|---|---|---|
| 1 | Rodar a Etapa 0 e colar a saída | Ildean |
| 2 | Responder as pendências P-01 a P-05 | Ildean |
| 3 | Apresentar o plano detalhado | Claude |

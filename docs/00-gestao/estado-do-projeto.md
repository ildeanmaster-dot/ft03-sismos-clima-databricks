# Estado do projeto
Versão 0.1 · 23/11/2026

| Etapa | Situação | O que falta |
|---|---|---|
| E0 Validação das APIs | Concluída (23/11/2026) | 224 eventos M5+ em out/2026; 3 sismos x 24 h de clima, 0 nulos |
| E1 Plano detalhado | Aprovado (23/11/2026) | `docs/02-arquitetura/plano-detalhado.md`; recomendações aceitas para P-01 a P-04, P-07 a P-09 |
| E2 Ambiente (catálogo, schemas, volumes, Git folder) | Concluída | Catálogo, schemas, volumes e Git folder criados; import de `src/` testado (OB-10 a OB-13); próxima: E3 extração |
| E3 Extração para bronze | Concluída | Out/2026 extraído: 224 sismos e 224 climas no volume `raw`, relatório sem falhas (OB-14 a OB-19); próxima: E4 bronze e silver |
| E4 Bronze e silver (desaninhamento SQL) | Concluída | Bronze, `silver.sismos` (224) e `silver.clima_horario` (5.376 = 224 x 24) criadas e conferidas (OB-20 a OB-25); próxima: E5 gold |
| E5 Gold (transformações e JOIN) | Concluída | `gold.sismo_clima_horario` com 5.376 linhas (224 x 24), T4 e T5, partição ano/mês e propriedade Snappy registrada (OB-27, OB-28); próxima: E6 qualidade |
| E6 Qualidade e relatório | Em andamento | Parte 1 concluída (OB-29); parte 2 concluída: `gold.qualidade_regras` com 10 regras aprovadas e teste com dados ruins em 6 delas (OB-30, OB-31); faltam `quality.py` com testes (Q-01, Q-03, Q-10) e o relatório JSON |
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

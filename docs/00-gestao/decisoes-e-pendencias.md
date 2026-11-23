# Decisões e pendências
Versão 0.1 · 23/11/2026

## 1. Decisões
| # | Decisão | Data | Situação |
|---|---|---|---|
| D-01 | APIs: USGS Earthquake (M5+, GeoJSON) + Open-Meteo Historical (horário) | 23/11/2026 | Aprovada pelo responsável |
| D-02 | Catálogo `ft03_sismos_clima` com schemas bronze/silver/gold | 23/11/2026 | Aprovada pelo responsável |
| D-03 | Projeto independente de `ft03-pipeline-energia-clima`, sem alterar aquele repositório | 23/11/2026 | Aprovada pelo responsável |
| D-04 | Repositório público na conta ildeanmaster-dot, criado pelo responsável | 23/11/2026 | Aprovada pelo responsável |
| D-05 | Tabela Delta gerenciada com `delta.parquet.compression.codec = SNAPPY` (UC managed nasce ZSTD) | 23/11/2026 | Proposta (doc table-properties, 17/11/2026) |

## 2. Pendências
| # | Pendência | Bloqueia | Com quem | Desde |
|---|---|---|---|---|
| P-01 | Período da extração (só out/2026 ou mais meses) | E3 | Ildean | 23/11/2026 |
| P-02 | Exportar o Parquet do gold e versionar a cópia em `output/` (o PDF pede `output/` com .parquet) | E8 | Ildean | 23/11/2026 |
| P-03 | "Clima no dia": dia UTC do evento (00h–23h UTC) ou outra janela | E3 | Ildean | 23/11/2026 |
| P-04 | Comando único: `databricks jobs run-now` pela CLI local, ou bundle | E7 | Ildean | 23/11/2026 |
| P-05 | Aceite de uma segunda entrega com outro tema pela turma | Entrega | Ildean | 23/11/2026 |
| P-06 | Valores e nulos do Open-Meteo em epicentro no oceano | E5 | Etapa 0 | 23/11/2026 |
| P-07 | JOIN: chave técnica `evento_id` (a consulta do clima usa coordenada + dia do evento) | E5 | Ildean | 23/11/2026 |
| P-08 | Módulos de `src/` no notebook: Git folder do GitHub ou importar pela CLI | E2 | Etapa 2 (teste) | 23/11/2026 |
| P-09 | Particionar ano/mês uma tabela de ~5 mil linhas: exigência do PDF contra boa prática de tabela pequena | E5 | Ildean | 23/11/2026 |

Aprovação do plano em 23/11/2026 ("aprovado"): P-01 (só out/2026), P-02 (exportar Parquet para `output/`), P-03 (dia UTC), P-04 (`run.sh` com `databricks jobs run-now`), P-07, P-08 (testar Git folder na E2) e P-09 seguem as recomendações. P-05 (aceite da turma) continua com o Ildean.

# Decisões e pendências
Versão 0.2 · 24/11/2026

## 1. Decisões
| # | Decisão | Data | Situação |
|---|---|---|---|
| D-01 | APIs: USGS Earthquake (M5+, GeoJSON) + Open-Meteo Historical (horário) | 23/11/2026 | Aprovada pelo responsável |
| D-02 | Catálogo `ft03_sismos_clima` com schemas bronze, silver e gold | 23/11/2026 | Aprovada pelo responsável |
| D-03 | Projeto independente de `ft03-pipeline-energia-clima`, sem alterar aquele repositório | 23/11/2026 | Aprovada pelo responsável |
| D-04 | Repositório público na conta ildeanmaster-dot, criado pelo responsável | 23/11/2026 | Aprovada pelo responsável |
| D-05 | Tabela Delta gerenciada com `delta.parquet.compression.codec = SNAPPY` (UC managed nasce ZSTD) | 23/11/2026 | Implementada (OB-28; Parquet exportado com Snappy no rodapé, OB-41) |
| D-06 | Corrigir o reprocessamento (DT-09) limpando `raw/usgs` e `raw/open_meteo` na extração, e não filtrando na bronze | 24/11/2026 | Implementada (OB-39) |
| D-07 | Período: só outubro de 2026 (P-01) | 23/11/2026 | Aprovada no plano |
| D-08 | Exportar o Parquet da gold e versionar a cópia em `output/` (P-02) | 23/11/2026 | Implementada (OB-43) |
| D-09 | "Clima no dia" = dia UTC do sismo, 00h a 23h UTC (P-03) | 23/11/2026 | Implementada (RN-02, RN-03) |
| D-10 | Comando único: `run.sh` com `databricks jobs run-now`, sem bundle (P-04) | 23/11/2026 | Implementada (OB-40) |
| D-11 | JOIN pela chave técnica `evento_id` (P-07) | 23/11/2026 | Implementada (OB-27) |
| D-12 | Módulos de `src/` no notebook por Git folder do GitHub (P-08) | 23/11/2026 | Implementada (OB-13) |
| D-13 | Particionar a gold por ano e mês mesmo com ~5 mil linhas, porque o PDF exige (P-09) | 23/11/2026 | Implementada (OB-28) |
| D-14 | Tarefa `exportacao` depois de `relatorio`: só publica com a qualidade aprovada | 24/11/2026 | Implementada (OB-42) |
| D-15 | Alterar o job com `databricks jobs reset` e o corpo local `jobs/ft03_pipeline_reset.local.json` (mantém o `job_id`) | 24/11/2026 | Implementada (OB-42) |
| D-16 | `.gitattributes` com `*.sh text eol=lf` para o `run.sh` funcionar num clone no Windows | 24/11/2026 | Implementada (OB-46) |
| D-17 | Versionar só o `.parquet` e o relatório; arquivos de controle do Databricks fora do Git | 24/11/2026 | Implementada (OB-43) |
| D-18 | Trocar o e-mail da OB-13 por `<e-mail do workspace>`; não reescrever o histórico | 24/11/2026 | Implementada |

## 2. Pendências
| # | Pendência | Bloqueia | Com quem | Desde |
|---|---|---|---|---|
| P-05 | Aceite de uma segunda entrega com outro tema pela turma (o prazo de 23/11/2026 08h00 já passou) | Entrega | Ildean | 23/11/2026 |

## 3. Pendências resolvidas
| # | Pendência | Como foi resolvida |
|---|---|---|
| P-01 | Período da extração | D-07 |
| P-02 | Exportar e versionar o Parquet em `output/` | D-08 |
| P-03 | Janela do "clima no dia" | D-09 |
| P-04 | Forma do comando único | D-10 |
| P-06 | Valores e nulos do Open-Meteo em epicentro no oceano | Out/2026: 0 nulos nas 5 variáveis em 5.376 horas (OB-29, OB-33); a regra Q-03 segue medindo a taxa de nulos |
| P-07 | Chave do JOIN | D-11 |
| P-08 | Módulos de `src/` no notebook | D-12 |
| P-09 | Particionar tabela pequena | D-13 |

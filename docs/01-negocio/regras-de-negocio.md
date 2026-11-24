# Regras de negócio
Versão 0.2 · 24/11/2026

Cada regra aponta o lugar do código que a implementa. Status: **Implementado** só com o local no código e a evidência de execução (OB).

## 1. Seleção de eventos
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-01 | Só terremotos com magnitude maior ou igual ao parâmetro `magnitude_minima` (padrão 5) | Pedido do responsável | Implementado (OB-22: `mag_min` = 5) | `src/sismos_clima/extract.py` (`filtros_usgs`, `minmagnitude`); conferida pela regra Q-06 |
| RN-02 | Data do evento = dia UTC de `properties.time` (milissegundos desde 1970) | Decisão D-09 (P-03) | Implementado (OB-23) | `sql/silver/01_silver.sql` (`data_utc`) e `extract.dia_utc` |
| RN-05 | Evento revisado pela USGS: fica a versão de maior `atualizado_em` | Risco R-04 | Implementado (OB-22) | `sql/silver/01_silver.sql` (`QUALIFY row_number()` por `evento_id`) |
| RN-06 | Sismo sem id, magnitude, instante ou coordenada é rejeitado e entra na contagem de rejeitados | Plano, T2 | Implementado (OB-33: 0 rejeitados em out/2026) | `sql/silver/01_silver.sql` (`WHERE`) e `quality_report.json` (`rejeitados`) |

## 2. Clima
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-03 | Clima horário no epicentro (latitude e longitude da USGS), 24 horas do dia UTC do sismo | Pedido do responsável | Implementado (OB-25: 24 horas por sismo) | `src/sismos_clima/extract.py` (`parametros_meteo`, `timezone=GMT`); conferida pela regra Q-09 |
| RN-04 | Chave do JOIN = id do evento (nome do arquivo de clima), nunca a coordenada devolvida, porque o Open-Meteo ajusta à grade | Teste 23/11/2026 (OB-08), decisão D-11 | Implementado (OB-27) | `sql/silver/01_silver.sql` (`regexp_extract` do nome do arquivo) e `sql/gold/01_gold.sql` (JOIN por `evento_id`) |
| RN-07 | Variável climática nula continua nula, sem preencher | Plano, T2 | Implementado (OB-29: 0 nulos em out/2026) | `sql/silver/01_silver.sql`; taxa de nulos na regra Q-03 (aviso) |

## 3. Métricas
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-08 | Faixa de magnitude só por intervalo numérico (`5.0 a 5.9`, `6.0 a 6.9`, `7.0 ou mais`), sem nome de classe | Plano (classificação nominal sem fonte oficial conferida) | Implementado (OB-28: 3 faixas) | `sql/gold/01_gold.sql` (`faixa_magnitude`) |
| RN-09 | Período da hora: `antes`, `hora do sismo` ou `depois`, pela diferença entre a hora do clima e a hora cheia do sismo | Plano, T5 | Implementado (OB-28: 224 linhas `hora do sismo`) | `sql/gold/01_gold.sql` (`horas_desde_sismo`, `periodo`) |

## 4. Publicação
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-10 | O Parquet só é publicado se nenhuma regra de qualidade de nível erro reprovar; o relatório é gravado antes, mesmo na falha | Plano, seção 4 | Implementado (OB-38: falha demonstrada; OB-42: `exportacao` depende de `relatorio`) | `notebooks/04_qualidade.py` (`exigir_aprovacao`) e `jobs/ft03_pipeline.json` |
| RN-11 | Reexecutar o mesmo período não duplica dados: tabelas recriadas, exportação em `overwrite` e `raw` limpo antes de gravar | Plano, seção 3; DT-09 | Implementado (OB-39, OB-43) | `CREATE OR REPLACE TABLE` nos SQL, `05_exportacao.py`, `extract.limpar_raw` |

## Resumo
11 regras, 11 Implementado.

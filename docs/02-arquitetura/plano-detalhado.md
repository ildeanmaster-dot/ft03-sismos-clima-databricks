# Plano detalhado
Versão 0.1 · 23/11/2026 · **Proposta para aprovação. Nada disto está implementado.**

## 1. Base: o que a Etapa 0 provou
| Fato | Evidência |
|---|---|
| Rede do Free Edition alcança USGS e Open-Meteo | HTTP 200 nas 4 células (OB-06 a OB-09) |
| Out/2026, M5+: 224 eventos; limite da USGS 20.000 por consulta | `count` = 224, `maxAllowed` = 20000 |
| GeoJSON: `time` em ms UTC, `coordinates` = [lon, lat, prof] | OB-07 |
| Open-Meteo devolve 24 horas em arrays paralelos e ajusta a coordenada à grade | OB-08 |
| 3 sismos x 24 horas de clima, 0 nulos | OB-09 |

Volume de chamadas previsto para out/2026: 1 count + 1 query + 224 de clima (uma por sismo) = 226. Cada chamada pede 1 dia e 5 variáveis, então conta como 1 chamada (regra de pesos do Open-Meteo, consultada em 23/11/2026). Isso é cerca de 2% do limite diário de 10.000.

## 2. Etapas
| Etapa | Entrega | Evidência de conclusão | Requisitos |
|---|---|---|---|
| E2 Ambiente | Catálogo `ft03_sismos_clima`, schemas `bronze`, `silver`, `gold`, volumes `bronze.raw` e `gold.export`; módulos de `src/` importáveis no notebook | `SHOW SCHEMAS`, `SHOW VOLUMES`, import sem erro | RNF-01 |
| E3 Extração | `config.py`, `http_client.py`, `extract.py`: JSON bruto no volume | arquivos no volume, 226 chamadas, relatório de extração | RF-01 a RF-04 |
| E4 Bronze e Silver | `sql/bronze`, `sql/silver`: leitura dos JSON e desaninhamento em SQL | contagens: 224 sismos, 5.376 linhas de clima | RF-05, RF-06 |
| E5 Gold | `sql/gold`: JOIN, métricas, `PARTITIONED BY (ano, mes)`, Snappy | contagem = sismos x 24; `SHOW TBLPROPERTIES` | RF-06, RF-09, RF-10 |
| E6 Qualidade | `quality.py` e notebook: regras Q-01 a Q-12, relatório JSON | relatório com status por regra | RF-07, RF-08 |
| E7 Job | Job com uma task por notebook; comando único | execução ponta a ponta com sucesso | RNF-04 |
| E8 Entrega | Export Parquet Snappy, testes, README, clone limpo | rodar o comando único num ambiente limpo | RF-09, RNF-01 a RNF-05 |
| E9 Portal (opcional) | Portal de acompanhamento no padrão Yottaflow | `portal/index.html` gerado | diretriz do responsável |

## 3. Tabelas
Padrão: uma tabela é recriada inteira a cada execução (`CREATE OR REPLACE TABLE`). Reexecutar o mesmo período dá o mesmo resultado, sem duplicar.

### Bronze (JSON bruto, sem transformação)
| Tabela | Grão | Conteúdo |
|---|---|---|
| `bronze.usgs_resposta` | 1 linha por resposta da USGS | `type`, `metadata`, `features` (array), `bbox`, `_arquivo`, `_lido_em` |
| `bronze.meteo_resposta` | 1 linha por sismo | `latitude`, `longitude`, `elevation`, `hourly_units`, `hourly` (struct de arrays), `_arquivo`, `_lido_em` |

Schema inferido pelo `read_files`. **A validar** (A1).

### Silver
`silver.sismos`, 1 linha por sismo, chave `evento_id`.
| Coluna | Tipo | Origem |
|---|---|---|
| evento_id | STRING | `features[].id` |
| magnitude | DOUBLE | `properties.mag` |
| tipo_magnitude | STRING | `properties.magType` |
| local | STRING | `properties.place` |
| instante_utc | TIMESTAMP | `properties.time` (ms) convertido |
| data_utc | DATE | cálculo sobre `instante_utc` |
| longitude, latitude | DOUBLE | `geometry.coordinates[0]`, `[1]` |
| profundidade_km | DOUBLE | `geometry.coordinates[2]` |
| status_revisao | STRING | `properties.status` |
| atualizado_em | TIMESTAMP | `properties.updated` (ms) convertido |
| arquivo_origem | STRING | `_arquivo` |

`silver.clima_horario`, 1 linha por sismo e hora, chave (`evento_id`, `hora_utc`).
| Coluna | Tipo | Origem |
|---|---|---|
| evento_id | STRING | extraído do nome do arquivo |
| hora_utc | TIMESTAMP | `hourly.time[i]` |
| temperatura_c | DOUBLE | `hourly.temperature_2m[i]` |
| umidade_pct | DOUBLE | `hourly.relative_humidity_2m[i]` |
| precipitacao_mm | DOUBLE | `hourly.precipitation[i]` |
| vento_kmh | DOUBLE | `hourly.wind_speed_10m[i]` |
| pressao_hpa | DOUBLE | `hourly.surface_pressure[i]` |
| latitude_grade, longitude_grade, elevacao_m | DOUBLE | resposta do Open-Meteo |

### Gold
`gold.sismo_clima_horario`, 1 linha por sismo e hora. `PARTITIONED BY (ano, mes)` pela data UTC do sismo. `TBLPROPERTIES ('delta.parquet.compression.codec' = 'SNAPPY')`.
| Coluna | Tipo | Tipo de coluna |
|---|---|---|
| evento_id, local | STRING | origem |
| ano, mes | INT | cálculo (de `data_utc`) |
| data_utc, instante_sismo_utc | DATE, TIMESTAMP | origem |
| magnitude, latitude, longitude, profundidade_km | DOUBLE | origem |
| hora_utc | TIMESTAMP | origem |
| temperatura_c, umidade_pct, precipitacao_mm, vento_kmh, pressao_hpa | DOUBLE | origem |
| faixa_magnitude | STRING | cálculo: `5.0 a 5.9`, `6.0 a 6.9`, `7.0 ou mais` |
| horas_desde_sismo | INT | cálculo: `hora_utc` menos a hora cheia do sismo |
| periodo | STRING | cálculo: `antes`, `hora do sismo`, `depois` |
| temp_media_dia_c, amplitude_termica_dia_c, precipitacao_total_dia_mm | DOUBLE | cálculo, por sismo |

As faixas de magnitude são só intervalos numéricos, sem nomes de classe, porque a classificação nominal não foi conferida em fonte oficial.

### As 5 transformações
| # | Transformação | Onde |
|---|---|---|
| T1 | Tipos e datas: ms para TIMESTAMP, texto ISO para TIMESTAMP, DOUBLE | silver |
| T2 | Nulos: sem chave, instante, coordenada ou magnitude, a linha vai para a contagem de rejeitados; `local` nulo vira `Não informado`; variável climática nula continua nula, sem preencher | silver |
| T3 | Deduplicação: por `evento_id`, fica o de maior `atualizado_em`; no clima, por (`evento_id`, `hora_utc`) | silver |
| T4 | JOIN `silver.sismos` com `silver.clima_horario` por `evento_id` | gold |
| T5 | Métricas: `horas_desde_sismo`, `periodo`, `faixa_magnitude`, média, amplitude e total do dia | gold |

Desaninhamento em SQL: `explode(features)` para os sismos e `posexplode(hourly.time)` com índice nas demais listas para o clima. A sintaxe exata é **A validar** (A8).

## 4. Regras de qualidade
Relatório em JSON: `gold.export/reports/quality_report.json`. Ele registra id e horário da execução, período, contagens por camada, resultado de cada regra, nulos por coluna e rejeitados.
| ID | Regra | Tipo | Nível |
|---|---|---|---|
| Q-01 | Colunas e tipos das 3 tabelas iguais ao schema deste plano | schema | erro |
| Q-02 | Sem nulos em `evento_id`, `instante_utc`, `magnitude`, `latitude`, `longitude` | null ratio | erro |
| Q-03 | Null ratio das 5 variáveis climáticas, por coluna, no relatório | null ratio | aviso |
| Q-04 | `evento_id` único em `silver.sismos` | unicidade | erro |
| Q-05a, Q-05b | (`evento_id`, `hora_utc`) único no clima (a) e no gold (b) | unicidade | erro |
| Q-06 | `magnitude` maior ou igual a 5 | intervalo | erro |
| Q-07 | Latitude entre -90 e 90, longitude entre -180 e 180 | intervalo | erro |
| Q-08 | Umidade entre 0 e 100; precipitação maior ou igual a 0 | intervalo | erro |
| Q-09 | 24 horas por sismo | completude | erro |
| Q-10 | Sismos na silver igual ao `count` da USGS | completude | erro |
| Q-11 | Linhas do gold igual a sismos x 24; nenhum sismo sem clima | JOIN | erro |
| Q-12 | Dia de `hora_utc` igual a `data_utc` do sismo | consistência | erro |

Limites físicos de temperatura, vento e pressão ficam fora: os dados reais foram vistos em 23/11/2026 (OB-29) e não há fonte oficial adotada para esses limites; eles aparecem só como informação no relatório. As regras em SQL gravam o resultado na tabela `gold.qualidade_regras` (`sql/quality/02_regras.sql`); `quality.py` lê essa tabela, soma Q-01 (schema), Q-03 (nulos por coluna) e Q-10 (contagem da USGS) e monta o relatório JSON. Política de falha: qualquer regra de nível erro reprova a task, o gold não é exportado e o relatório continua salvo.

## 5. Extração: taxa e retentativas
| Item | Valor proposto | Base |
|---|---|---|
| Intervalo mínimo entre chamadas, USGS | 1 s | limite numérico não publicado; valor conservador |
| Intervalo mínimo, Open-Meteo | 0,5 s | máximo de 120 por minuto, contra o limite de 600 |
| Erros com nova tentativa | 429, 500, 502, 503, 504, timeout, falha de conexão | |
| Tentativas | até 5, espera 1, 2, 4, 8 s mais variação aleatória; respeita `Retry-After` | |
| Sem nova tentativa | 400 e demais 4xx | erro permanente |
| Tempo limite | 10 s para conectar, 30 s para ler | Etapa 0 |

## 6. Orquestração e comando único
Job com 6 tasks em sequência: extração, bronze e silver, gold, qualidade, exportação. Parâmetros: `data_inicio`, `data_fim`, `magnitude_minima`. O job é descrito num JSON versionado e criado pela CLI. `run.sh` chama `databricks jobs run-now`. Sem bundles e sem pipeline declarativo, para manter o nível simples. Execução em 5 tasks concorrentes ou menos, dentro do limite do Free Edition.

## 7. Exportação
Gold lido em Spark e gravado em Parquet Snappy, particionado por ano e mês, em `gold.export/dataset/`. A prova de Snappy é o rodapé do arquivo Parquet. Depois, `databricks fs cp -r` copia para `output/`.

## 8. A validar durante a execução
| # | Item |
|---|---|
| A1 | `read_files` com JSON aninhado no serverless (resolvida em 23/11/2026, OB-20) |
| A2 | Git folder ou import dos módulos no notebook (resolvida em 23/11/2026, OB-13) |
| A3 | `SNAPPY` na propriedade da tabela gerenciada (propriedade aceita e registrada em 23/11/2026, OB-28; a prova no rodapé do arquivo Parquet fica para a exportação, E8) |
| A4 | `partitionBy` ao gravar Parquet no volume |
| A5 | Parâmetros do job chegando aos notebooks |
| A6 | `CREATE CATALOG` no seu workspace (resolvida em 23/11/2026, OB-10) |
| A7 | Limite numérico de taxa da USGS |
| A8 | Sintaxe de `posexplode` com índice nas demais listas (resolvida em 23/11/2026, OB-24) |
| A9 | `endtime` da USGS recebendo só a data: confirmar se o limite é 00:00 UTC do dia informado (por isso a config usa o dia seguinte ao fim, `data_fim_exclusiva`) |
| A10 | Diretório atual de um notebook dentro do Git folder no serverless (resolvida em 23/11/2026, OB-19) |

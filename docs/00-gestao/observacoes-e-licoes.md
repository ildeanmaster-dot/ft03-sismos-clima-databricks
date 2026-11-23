# Observações e lições
Versão 0.1 · 23/11/2026

| # | Observação | O que fizemos | Fonte |
|---|---|---|---|
| OB-01 | No Free Edition, a saída de rede só alcança alguns domínios; USGS e Open-Meteo Archive estão liberados, IBGE, BCB, ONS e outros estão bloqueados | Escolha das APIs pelo teste | Teste do responsável no workspace, 23/11/2026 |
| OB-02 | Tabela Delta gerenciada no UC nasce com ZSTD | Snappy via `TBLPROPERTIES` | docs.databricks.com tables/table-properties, 17/11/2026 |
| OB-03 | USGS limita 20.000 eventos por consulta; acima disso HTTP 400 | Usar o método `count` antes da consulta | earthquake.usgs.gov/fdsnws/event/1/docs.html, consultado 23/11/2026 |
| OB-04 | Open-Meteo: consulta com mais de 10 variáveis ou mais de 2 semanas conta como várias chamadas | Até 10 variáveis e 1 dia por consulta | open-meteo.com/en/pricing, consultado 23/11/2026 |
| OB-05 | ERA5 e ERA5-Land têm atraso de 5 dias | Período sempre anterior a hoje − 5 dias | open-meteo.com/en/docs/historical-weather-api, consultado 23/11/2026 |

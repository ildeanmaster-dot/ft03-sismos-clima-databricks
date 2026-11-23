# Arquitetura da solução
Versão 0.1 · 23/11/2026 · **Proposta, a detalhar no plano**

| Camada | Objeto (Unity Catalog) | Conteúdo |
|---|---|---|
| Landing | volume `ft03_sismos_clima.bronze.raw` | JSON bruto das 2 APIs |
| Bronze | tabelas com o JSON bruto e metadados de ingestão | |
| Silver | sismos (1 linha por evento) e clima horário (1 linha por evento × hora) | desaninhamento em SQL |
| Gold | sismo × clima | JOIN, métricas, `PARTITIONED BY (ano, mes)`, Snappy |
| Qualidade | relatório JSON no volume | schema, null ratio, unicidade, intervalo |

Orquestração: Lakeflow Job com uma task por notebook (até 5 tasks concorrentes no Free Edition).

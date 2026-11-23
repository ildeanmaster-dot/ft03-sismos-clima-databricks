# FT03 – Sismos × Clima no Databricks

> **Status: em desenvolvimento (23/11/2026).** Estrutura do repositório criada; a Etapa 0 (validação das APIs) está em `notebooks/00_validacao_apis.py`. O pipeline será implementado depois da aprovação do plano. O que ainda não foi testado está marcado como **A validar**.

Segunda entrega do **Desafio Python – FT03 – Projeto 1**, com outro tema. É independente do projeto [`ft03-pipeline-energia-clima`](https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima).

## Objetivo
Pipeline simples que cruza **terremotos de magnitude 5 ou mais** (USGS) com o **clima horário no epicentro, no dia do evento** (Open-Meteo Historical), em arquitetura medalhão (bronze/silver/gold) no Unity Catalog do **Databricks Free Edition** (serverless, Python e SQL).

## APIs utilizadas
| API | Domínio | Endpoint | Autenticação | Limites publicados |
|---|---|---|---|---|
| USGS Earthquake Catalog (FDSN Event) | Sismologia | `https://earthquake.usgs.gov/fdsnws/event/1/query` | não exige | até **20.000 eventos por consulta**; acima disso HTTP 400 (docs.html, consultado 23/11/2026). Limite de taxa numérico **não publicado**; excesso devolve HTTP 429 (aviso da lista realtime-feeds, jan/2022) |
| Open-Meteo Historical Weather | Meteorologia | `https://archive-api.open-meteo.com/v1/archive` | não exige (plano gratuito) | **600/min, 5.000/h, 10.000/dia, 300.000/mês**; consulta com mais de 10 variáveis ou mais de 2 semanas conta como várias chamadas; só uso não comercial; CC BY 4.0 (open-meteo.com/en/terms e /en/pricing, consultado 23/11/2026) |

Saída de rede do Free Edition para os dois domínios: liberada em teste real no workspace (23/11/2026).

## Arquitetura (prevista — A validar no plano)
```
USGS (GeoJSON) ─┐                         ┌─> silver.sismos (features[] desaninhado em SQL)
                ├─> volume bronze.raw ────┤
Open-Meteo ─────┘   (JSON bruto)          └─> silver.clima_horario (arrays hourly desaninhados em SQL)
                                                     │
                                         gold.sismo_clima (JOIN por coordenada + data)
                                                     │
                       relatório de qualidade (JSON) + export Parquet Snappy (ano/mês)
```
Catálogo Unity Catalog: `ft03_sismos_clima` (schemas `bronze`, `silver`, `gold`).

## Estrutura do repositório
| Caminho | Conteúdo |
|---|---|
| `src/sismos_clima/` | Pacote Python modular e tipado (configuração, cliente HTTP, extração, qualidade) |
| `notebooks/` | Notebooks do Databricks, um por etapa do job |
| `sql/` | SQL de bronze, silver e gold (desaninhamento e transformações) |
| `tests/` | Testes com amostras pequenas (fixtures) |
| `output/` | Dataset final em Parquet e relatório de qualidade |
| `docs/` | Documentação de negócio, técnica, regras e débito técnico |
| `config/` | Parâmetros não secretos |

## Como executar
**A validar** — definido no plano. Previsto: um job do Databricks que encadeia os notebooks, disparado por um comando (`run.sh`).

## Variáveis de ambiente
Ver `.env.example`. As duas APIs não usam chave. Nenhum segredo é versionado.

## Requisitos do desafio × situação
Ver `docs/01-negocio/requisitos.md`.

## Licenças dos dados
- USGS: dado do governo dos EUA (domínio público) — **A validar** na página de política da USGS.
- Open-Meteo: CC BY 4.0, atribuição obrigatória; plano gratuito só para uso não comercial.

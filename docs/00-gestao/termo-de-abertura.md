# Termo de abertura
Versão 0.1 · 23/11/2026

| Campo | Valor |
|---|---|
| Projeto | FT03 – Sismos × Clima no Databricks |
| Responsável | Ildean Freitas |
| Contexto | Segunda entrega do Desafio Python – FT03 – Projeto 1, com outro tema; independente de `ft03-pipeline-energia-clima` (entregue em 23/11/2026, não alterar) |
| Ambiente | Databricks Free Edition (serverless; Python e SQL; sem Scala) |
| Repositório | `ildeanmaster-dot/ft03-sismos-clima-databricks` (público) |

## Objetivo
Cruzar terremotos de magnitude 5 ou mais (USGS) com o clima horário no epicentro no dia do evento (Open-Meteo Historical), em medalhão bronze/silver/gold no Unity Catalog, com desaninhamento e transformações em SQL, relatório de qualidade e um job que encadeia tudo.

## Escopo
| Dentro | Fora |
|---|---|
| 2 APIs (USGS, Open-Meteo), rate limit e retentativas, Python modular e tipado, SQL de desaninhamento, 5 transformações, relatório de qualidade, Delta/Parquet Snappy particionado por ano/mês, job, README | Análise estatística de causalidade sismo × clima; streaming; bundles e CI/CD (A validar) |

## Entregas e critério de aceite
| Entrega | Critério |
|---|---|
| Etapa 0 — validação das APIs | 3 sismos de out/2026 com 24 horas de clima cada, em execução real no workspace |
| Plano detalhado | Aprovado pelo responsável |
| Pipeline | Matriz de requisitos (`01-negocio/requisitos.md`) toda com evidência |

## Premissas e restrições
- Saída de rede liberada para `earthquake.usgs.gov` e `archive-api.open-meteo.com` (teste real, 23/11/2026).
- Free Edition: uso pessoal, sem Scala, sem cache, 5 tasks concorrentes por conta.
- Open-Meteo gratuito: só uso não comercial.

## Aprovação
| Papel | Nome | Data |
|---|---|---|
| Responsável | | |

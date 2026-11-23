# Regras de negócio
Versão 0.1 · 23/11/2026

## 1. Seleção de eventos
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-01 | Só terremotos com magnitude ≥ 5 (`minmagnitude=5`) | Pedido do responsável | Pendente | Extração |
| RN-02 | Data do evento = data UTC de `properties.time` (epoch em ms) | A validar (P-03) | Provisório | Silver |

## 2. Clima
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-03 | Clima horário no ponto do epicentro (lat/lon da USGS), 24 horas do dia do evento | Pedido do responsável | Pendente | Extração |
| RN-04 | Chave do JOIN = id do evento enviado na consulta, não a coordenada devolvida (o Open-Meteo ajusta à grade) | Lição do projeto energia-clima (teste 12/11/2026) | Provisório | Gold |

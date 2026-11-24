# Diagramas
Versão 0.2 · 24/11/2026

## Extração resiliente
Uma chamada `count` e uma `query` na USGS, depois uma chamada ao Open-Meteo por sismo. O cliente HTTP espera o intervalo mínimo antes de cada chamada e repete só erros transitórios (429, 5xx, timeout), respeitando `Retry-After`.
```mermaid
sequenceDiagram
  participant N as 01_extracao_bronze
  participant U as USGS
  participant R as volume raw
  participant M as Open-Meteo
  N->>U: count (período e magnitude)
  U-->>N: 224 sismos, máximo 20000
  N->>U: query GeoJSON
  U-->>N: features com 224 sismos
  N->>R: apaga os JSON antigos (limpar_raw)
  N->>R: grava eventos_inicio_fim.json
  loop um por sismo, 0,5 s entre chamadas
    N->>M: clima do epicentro no dia UTC
    M-->>N: 24 horas em listas paralelas
    N->>R: grava evento_id.json
  end
  N->>R: grava extracao_relatorio.json
```

## Desaninhamento do clima em SQL
O Open-Meteo devolve uma lista por variável, todas na mesma ordem. `posexplode(hourly.time)` cria uma linha por hora e guarda a posição; a posição lê o valor de cada lista.
```mermaid
flowchart LR
  A["hourly.time: 00h, 01h, ... 23h<br/>hourly.temperature_2m: 21.7, 23.4, ...<br/>hourly.relative_humidity_2m: 37, 34, ..."] --> P["posexplode(hourly.time)<br/>pos 0 a 23"]
  P --> L0["pos 0: 00h, 21.7 °C, 37%"]
  P --> L1["pos 1: 01h, 23.4 °C, 34%"]
  P --> LN["... pos 23: 23h"]
```

## Política de falha da qualidade
O relatório é gravado antes da decisão. Uma regra de nível erro reprovada derruba a tarefa `relatorio`, e a `exportacao` não roda.
```mermaid
flowchart TB
  R["02_regras: 10 regras SQL"] --> Q["04_qualidade: schema, nulos e contagem USGS"]
  Q --> W["grava quality_report.json"]
  W --> D{"alguma regra de<br/>nível erro reprovou?"}
  D -->|não| E["exportacao roda<br/>Parquet publicado"]
  D -->|sim| F["tarefa relatorio falha<br/>Parquet não é publicado"]
  classDef ok fill:#E8F3EA,stroke:#427751,color:#13293D
  classDef ruim fill:#FBE9E6,stroke:#D43416,color:#13293D
  class E ok
  class F ruim
```

## Reprocessamento sem duplicar
Lição da OB-38: antes da correção, o volume `raw` guardava o arquivo de um período anterior e a bronze lia os dois.
```mermaid
flowchart TB
  subgraph Antes["Antes (A5, 24/11/2026)"]
    direction LR
    A1["raw: arquivo de 01 a 31/10<br/>+ arquivo de 01 a 15/10"] --> A2["bronze: 313 eventos"]
    A2 --> A3["Q-10 reprovou<br/>89 contra 224"]
  end
  subgraph Depois["Depois (DT-09)"]
    direction LR
    B1["limpar_raw apaga os JSON antigos<br/>depois que a USGS responde"] --> B2["raw: só o período pedido"]
    B2 --> B3["bronze: 224 eventos<br/>15 de 15 regras"]
  end
  Antes ~~~ Depois
```

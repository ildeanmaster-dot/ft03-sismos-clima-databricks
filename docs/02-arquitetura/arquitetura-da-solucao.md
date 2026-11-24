# Arquitetura da solução
Versão 0.2 · 24/11/2026 · como construído (as-built)

| Camada | Objeto (Unity Catalog) | Conteúdo | Evidência |
|---|---|---|---|
| Landing | volume `ft03_sismos_clima.bronze.raw` | JSON bruto das 2 APIs e `extracao_relatorio.json` | OB-19, OB-39 |
| Bronze | `bronze.usgs_resposta`, `bronze.meteo_resposta` | JSON lido com `read_files`, sem transformação, com `_arquivo` e `_lido_em` | OB-20, OB-21 |
| Silver | `silver.sismos`, `silver.clima_horario` | desaninhamento em SQL, tipos, nulos e deduplicação | OB-22 a OB-25 |
| Gold | `gold.sismo_clima_horario` | JOIN por `evento_id` e métricas; `PARTITIONED BY (ano, mes)`; Snappy | OB-27, OB-28 |
| Qualidade | `gold.qualidade_regras` e `gold.export/reports/quality_report.json` | schema, nulos, unicidade, intervalos, completude | OB-30 a OB-33 |
| Exportação | volume `gold.export/dataset` e `output/` no Git | Parquet Snappy particionado | OB-41, OB-43 |

Execução: Databricks Free Edition, serverless, Python e SQL. Orquestração: um job com 7 tarefas em sequência, disparado por `run.sh`.

## 1. Visão geral da solução
Das duas APIs até o Parquet no repositório. As setas mostram o caminho do dado.
```mermaid
flowchart TB
  U["USGS<br/>GeoJSON M5+"] --> X["01_extracao_bronze<br/>Python"]
  M["Open-Meteo<br/>clima horário"] --> X
  X --> R[("volume<br/>bronze.raw")]
  R --> B["bronze<br/>read_files"]
  B --> S["silver<br/>explode e posexplode"]
  S --> G["gold<br/>JOIN e métricas"]
  G --> Q["qualidade<br/>15 regras"]
  Q -->|aprovada| E["05_exportacao<br/>Parquet Snappy"]
  E --> V[("volume<br/>gold.export")]
  V -->|databricks fs cp| O["output/ no GitHub"]
  classDef api fill:#E3EEF6,stroke:#1F5F8B,color:#13293D
  classDef arm fill:#FFFFFF,stroke:#1F5F8B,color:#13293D
  class U,M api
  class R,V,O arm
```

## 2. Orquestração: job de 7 tarefas
Job `ft03-sismos-clima-pipeline` (`jobs/ft03_pipeline.json`). Cada tarefa só começa se a anterior terminar com sucesso.
```mermaid
flowchart TB
  T1["extracao<br/>notebooks/01_extracao_bronze"] --> T2["bronze<br/>sql/bronze/01_bronze"]
  T2 --> T3["silver<br/>sql/silver/01_silver"]
  T3 --> T4["gold<br/>sql/gold/01_gold"]
  T4 --> T5["regras<br/>sql/quality/02_regras"]
  T5 --> T6["relatorio<br/>notebooks/04_qualidade"]
  T6 --> T7["exportacao<br/>notebooks/05_exportacao"]
  RS(["run.sh<br/>jobs run-now"]) -.-> T1
```

## 3. Modelo de dados
Uma linha da gold = um sismo numa hora UTC do dia do sismo. Chave: (`evento_id`, `hora_utc`).
```mermaid
erDiagram
  SILVER_SISMOS ||--|{ SILVER_CLIMA_HORARIO : "evento_id, 24 horas"
  SILVER_SISMOS ||--|{ GOLD_SISMO_CLIMA_HORARIO : "evento_id"
  SILVER_SISMOS {
    string evento_id PK
    double magnitude
    timestamp instante_utc
    date data_utc
    double latitude
    double longitude
    double profundidade_km
  }
  SILVER_CLIMA_HORARIO {
    string evento_id PK
    timestamp hora_utc PK
    double temperatura_c
    double umidade_pct
    double precipitacao_mm
    double vento_kmh
    double pressao_hpa
  }
  GOLD_SISMO_CLIMA_HORARIO {
    string evento_id PK
    timestamp hora_utc PK
    int ano
    int mes
    string faixa_magnitude
    int horas_desde_sismo
    string periodo
    double temp_media_dia_c
  }
```

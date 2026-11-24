# Testes

34 testes com pytest, sem chamada de rede (sessões HTTP falsas e pastas temporárias):

| Arquivo | Testes | O que cobre |
|---|---|---|
| `test_http_client.py` | 8 | sucesso, 429 com Retry-After, 5xx com backoff e teto, timeout, erro permanente sem repetir, esgotamento, Retry-After longo demais, limitador de taxa |
| `test_extract.py` | 13 | parâmetros da USGS e do Open-Meteo, dia UTC, gravação dos arquivos e do relatório, falha de um clima, limite de 20.000, id inválido, limpeza do `raw` (DT-09) |
| `test_quality.py` | 13 | schema (Q-01), status das regras, taxa de nulos (Q-03), contagem USGS (Q-10), montagem e gravação do relatório, política de falha |

Como rodar (na raiz do repositório):

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/python -m pytest tests                # Windows: .venv\Scripts\python -m pytest tests
```

Resultado em 24/11/2026: `34 passed` (Python 3.10.12, OB-45). As regras em SQL são testadas no Databricks pelas células de teste negativo de `sql/quality/02_regras.sql` (OB-31, OB-44).

# Roteiro de execução da apresentação
Versão 0.1 · 24/11/2026 · comandos para rodar ao vivo, na ordem. Todos foram executados em 24/11/2026 no Windows do responsável (PowerShell, perfil `ft03`).

Regras para a apresentação:
- Um comando por vez. Espere o prompt `PS D:\...>` voltar antes do próximo.
- Não use a seta para cima para repetir um comando com argumento diferente.
- O aviso "Databricks CLI v1.17.0 found... Executing CLI v1.17.0" é normal: é o redirecionamento do 0.18 do pip.

## 0. Apresentação só pelo Databricks (sem terminal)
Testado em 24/11/2026 (OB-50). Tudo fica no workspace:

| # | Onde | O que fazer | Resultado esperado |
|---|---|---|---|
| W1 | Workspace → Home → Drafts → `ft03-sismos-clima-databricks` → botão `main` → **Pull** | Deixa o Git folder igual ao GitHub | Pull sem conflito |
| W2 | **Jobs & Pipelines** → `ft03-sismos-clima-pipeline` → **Run now** | Dispara o pipeline (cerca de 4 min 35 s) | Execução nova, lançamento `Manually`, 7 tarefas `Succeeded` |
| W3 | Git folder → `notebooks/validacao_do_pipeline`, compute **Serverless**, **Run all** | Notebook de validação: descrição de cada camada e consultas que conferem o resultado, todas só de leitura | Mesmos números das OB-50 (224, 5.376, 15/15, SNAPPY) |
| W4 | Página da execução: abas **List**, **Graph** e **Timeline**; painel **Parameters** | Mostra o resultado e o tempo de cada tarefa | 7 tarefas `Succeeded` |
| W5 | Opcional: seta ao lado de Run now → **Run now with different parameters** → `data_inicio` 2026-10-31, `data_fim` 2026-10-01 | Falha controlada, sem alterar dados | `extracao` falha, as outras 6 não rodam |

Cuidados: não execute as células de `01_extracao_bronze` (a célula Executar extração chama as APIs e limpa o `raw`) nem a célula 2 de `05_exportacao` (regrava o Parquet); notebook Python precisa de **Serverless**, não de SQL warehouse; os notebooks soltos na Home (`00_validacao_apis`, `01_ambiente`, `02_teste_import`, `03_explorar_bronze`) são rascunhos fora do Git.

## 1. Antes da apresentação pelo terminal (no dia, uma vez)
| # | Comando | O que faz | Resultado esperado |
|---|---|---|---|
| A1 | `cd D:\Portifolio\DesafioPythonFT03SismosClima` | Entra na pasta do projeto | Prompt `PS D:\Portifolio\DesafioPythonFT03SismosClima>` |
| A2 | `git pull` | Traz a última versão do GitHub | `Already up to date.` ou a lista do que mudou |
| A3 | `databricks current-user me -p ft03` | Confere se o login da CLI no workspace está válido | JSON com o seu usuário. Se der erro de token: `databricks auth login --host https://dbc-c699beda-0bbc.cloud.databricks.com --profile ft03` |
| A4 | No Databricks: Git folder `ft03-sismos-clima-databricks`, botão `main`, **Pull** | Deixa os notebooks do workspace iguais ao GitHub | Pull sem conflito |
| A5 | `python -m venv .venv` | Cria o ambiente dos testes (só se a pasta `.venv` não existir) | Sem saída |
| A6 | `.venv\Scripts\pip install -r requirements.txt` | Instala requests 2.34.2, urllib3 2.8.0 e pytest 9.2.0 | `Successfully installed ...` |
| A7 | Abrir `portal\index.html` no navegador | Portal com a apresentação técnica e a execução animada | Painel com 11/11, 10/10, 1 pendência, 5 débitos |

## 2. Durante a apresentação pelo terminal
Ordem sugerida: dispare o pipeline (passo 1) logo no começo, porque leva de 4 a 5 minutos (265 a 311 s nas execuções de 24/11/2026). Enquanto ele roda, mostre a **Execução animada** e as partes 1 a 8 da **Apresentação técnica**.

| # | Comando ou lugar | O que faz | Resultado esperado | Parte da apresentação |
|---|---|---|---|---|
| 1 | `& "C:\Program Files\Git\bin\bash.exe" run.sh` | Comando único: dispara o job de 7 tarefas e espera o fim | 1ª linha `Disparando o job com jobs/run_padrao.json (perfil ft03)...`; no fim, JSON com `"result_state": "SUCCESS"` e `Execução terminada com SUCCESS.` | 9 Orquestração |
| 2 | `$LASTEXITCODE` | Mostra o código de saída do comando único | `0` | 9 Orquestração |
| 3 | `databricks fs cat "dbfs:/Volumes/ft03_sismos_clima/bronze/raw/extracao_relatorio.json" -p ft03` | Lê o relatório da extração | `count_usgs` 224, `climas_gravados` 224, `falhas` vazio, `completo` true, `arquivos_antigos_removidos` 225 (1 arquivo da USGS e 224 de clima da execução anterior) | 4 Extração, 10 Reprocessamento |
| 4 | `databricks fs ls "dbfs:/Volumes/ft03_sismos_clima/bronze/raw/usgs" -p ft03` | Mostra que o `raw` só tem o período pedido | Uma linha: `eventos_2026-10-01_2026-10-31.json` | 10 Reprocessamento |
| 5 | `databricks fs cat "dbfs:/Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json" -p ft03 \| Out-String \| ConvertFrom-Json \| Select-Object iniciado_em_utc, periodo, contagens, resumo, aprovado \| Format-List` | Resumo do relatório de qualidade | `contagens` com 224 e 5376; `resumo` 15 regras, 15 aprovadas; `aprovado` True | 7 Qualidade |
| 6 | Databricks: `sql/gold/01_gold`, célula **Ver a virada antes e depois do sismo** | Mostra `horas_desde_sismo` -1, 0, 1 e `periodo` antes, hora do sismo, depois | 3 linhas do sismo `aka2026tuxgky` | 6 Gold |
| 7 | Databricks: `sql/gold/01_gold`, célula **Ver propriedades da gold (A3)** | Mostra a propriedade Snappy da tabela | `delta.parquet.compression.codec` = `SNAPPY` | 6 Gold |
| 8 | Databricks: `sql/quality/02_regras`, célula **Testar Q-05a, Q-05b, Q-09 e Q-11 com dados ruins** | Teste negativo: as regras acham defeito em dados inventados | 4 linhas `detectou` (1, 2, 2 e 25) | 7 Qualidade |
| 9 | Databricks: `notebooks/05_exportacao`, células **Listar os arquivos gravados** e **Provar o Snappy no rodapé do Parquet** | Mostra a partição e a compressão gravada no arquivo | `ano=2026/mes=10/...snappy.parquet`; `compressões no rodapé: {'SNAPPY'}` | 8 Exportação |
| 10 | `.venv\Scripts\python -m pytest tests` | Roda os 34 testes unitários, sem rede | `34 passed` | 4 Extração, 11 Resultados |
| 11 | `git ls-files --eol run.sh` | Mostra que o `run.sh` fica com LF por causa do `.gitattributes` | `i/lf w/lf attr/text eol=lf run.sh` | 11 Resultados |

## 3. Demonstração de falha (opcional, cerca de 2 minutos)
Mostra que o comando único avisa quando o job falha. É segura: a tarefa `extracao` recebe um período invertido e para antes de chamar as APIs; `raw`, tabelas e `output/` não mudam.

| # | Comando | O que faz | Resultado esperado |
|---|---|---|---|
| F1 | `& "C:\Program Files\Git\bin\bash.exe" run.sh jobs/teste_falha_parametros.json` | Dispara o job com início 31/10 e fim 01/10 | `Error: failed to reach TERMINATED or SKIPPED ... Task extracao failed ...` e `O job não terminou em SUCCESS.` |
| F2 | `$LASTEXITCODE` | Código de saída da falha | `1` |

Motivo: o `databricks` do PATH (0.18 do pip) devolvia 0 numa falha; o `run.sh` confere o `result_state` e sai com 1 (OB-47).

## 4. Se algo der errado
| Sintoma | O que fazer |
|---|---|
| `refresh token` inválido ou erro de autenticação | `databricks auth login --host https://dbc-c699beda-0bbc.cloud.databricks.com --profile ft03`; nunca usar o perfil DEFAULT, que aponta para outro workspace |
| `bash: $'\r': command not found` | O `run.sh` ficou com CRLF; conferir com `git ls-files --eol run.sh` |
| O job demora mais de 20 minutos | A CLI para de esperar (`--timeout` padrão de 20 min); acompanhe pela página Jobs & Pipelines do workspace |
| Pull com marcador `<<<<<<<` no Git folder | Usar **Abort**; nunca Continue merge nem Reset |

## 5. Depois da apresentação (só se quiser atualizar o `output/`)
| # | Comando | O que faz |
|---|---|---|
| D1 | `databricks fs cp -r "dbfs:/Volumes/ft03_sismos_clima/gold/export/dataset" output\dataset --overwrite -p ft03` | Copia o Parquet da última execução para `output/` |
| D2 | `databricks fs cp "dbfs:/Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json" output\reports\quality_report.json --overwrite -p ft03` | Copia o relatório da mesma execução |
| D3 | `python portal/gerar_portal.py` | Regera o portal com os documentos atuais |

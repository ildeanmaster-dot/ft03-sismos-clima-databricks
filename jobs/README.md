# jobs/

**O que faz:** guarda a definição do job do Databricks e os corpos de execução usados pelo `run.sh`.

**O que contém:**
- `ft03_pipeline.json`: modelo do job `ft03-sismos-clima-pipeline`, com 7 tarefas encadeadas (extracao, bronze, silver, gold, regras, relatorio, exportacao) e 4 parâmetros (`data_inicio`, `data_fim`, `magnitude_minima`, `catalogo`). O texto `{{RAIZ_GIT}}` é trocado pelo caminho da Git folder no workspace.
- `run_padrao.json`: corpo do `run-now` com o período padrão (01 a 31/10/2026).
- `teste_a5_parametros.json`: execução com `data_fim` 2026-10-15, para provar que os parâmetros chegam às tarefas.
- `teste_falha_parametros.json`: período invertido de propósito; a tarefa `extracao` falha antes de chamar as APIs e as outras 6 não rodam.
- `*.local.json` (fora do Git, ver `.gitignore`): versões com o caminho real do workspace.

**Resultado esperado:** `bash run.sh` com `run_padrao.json` termina com as 7 tarefas em `SUCCESS`; com `teste_falha_parametros.json` o `run.sh` devolve código 1.

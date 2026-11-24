#!/usr/bin/env bash
# Comando único do projeto: dispara o job ft03-sismos-clima-pipeline no Databricks e espera o fim.
# Pré-requisitos: Databricks CLI 0.218 ou mais nova e um perfil autenticado (padrão: ft03).
# Uso: bash run.sh                          (perfil ft03, corpo jobs/run_padrao.json)
#      PERFIL=outro bash run.sh             (outro perfil da CLI)
#      bash run.sh jobs/outro_corpo.json    (outro corpo do run-now, por exemplo com job_parameters)
set -euo pipefail  # para no primeiro erro, em variável não definida e em falha dentro de pipe

PERFIL="${PERFIL:-ft03}"  # perfil da CLI; a variável de ambiente PERFIL troca o padrão
CORPO="${1:-jobs/run_padrao.json}"  # corpo do run-now; o 1º argumento troca o padrão
cd "$(dirname "$0")"  # vai para a raiz do repositório, onde fica a pasta jobs/

echo "Disparando o job com ${CORPO} (perfil ${PERFIL})..."  # avisa o que vai rodar
saida="$(databricks jobs run-now --json "@${CORPO}" -p "${PERFIL}")"  # sem --no-wait: espera o fim; com set -e, erro da CLI encerra aqui
echo "${saida}"  # mostra o JSON da execução
estado="$(grep -o '"result_state": *"[A-Z_]*"' <<< "${saida}" | head -n 1 || true)"  # 1ª ocorrência = estado da execução inteira (vem antes de "tasks")
if [[ "${estado}" != *'"SUCCESS"'* ]]; then  # sem SUCCESS no estado geral, o pipeline não terminou bem
  echo "O job não terminou em SUCCESS." >&2  # mensagem de erro
  exit 1  # sinaliza a falha mesmo que a CLI tenha devolvido 0 (OB-47)
fi
echo "Execução terminada com SUCCESS. Relatório: /Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json"  # onde conferir o resultado

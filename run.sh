#!/usr/bin/env bash
# Comando único do projeto: dispara o job ft03-sismos-clima-pipeline no Databricks e espera o fim.
# Pré-requisitos: Databricks CLI 0.218 ou mais nova e um perfil autenticado (padrão: ft03).
# Uso: bash run.sh               (perfil ft03, parâmetros padrão do job)
#      PERFIL=outro bash run.sh  (outro perfil da CLI)
set -euo pipefail  # para no primeiro erro, em variável não definida e em falha dentro de pipe

PERFIL="${PERFIL:-ft03}"  # perfil da CLI; a variável de ambiente PERFIL troca o padrão
cd "$(dirname "$0")"  # vai para a raiz do repositório, onde fica a pasta jobs/

echo "Disparando o job com jobs/run_padrao.json (perfil ${PERFIL})..."  # avisa o que vai rodar
databricks jobs run-now --json @jobs/run_padrao.json -p "${PERFIL}"  # sem --no-wait: espera TERMINATED ou SKIPPED (limite padrão 20 min)
echo "Execução terminada. Relatório: /Volumes/ft03_sismos_clima/gold/export/reports/quality_report.json"  # onde conferir o resultado

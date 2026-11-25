# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Resumo do arquivo
# MAGIC %md
# MAGIC # 01_extracao_bronze
# MAGIC **O que faz:** extrai os dados das duas APIs e grava o JSON bruto no volume `bronze.raw`. É a primeira tarefa (`extracao`) do job. O notebook é fino: a lógica está em `src/sismos_clima` (config, http_client, extract).
# MAGIC
# MAGIC **O que contém:**
# MAGIC - leitura dos parâmetros do job (`data_inicio`, `data_fim`, `magnitude_minima`, `catalogo`)
# MAGIC - chamada de `extrair`, que consulta a USGS (count e eventos) e, para cada sismo, o Open-Meteo do dia UTC no epicentro
# MAGIC - limpeza dos .json antigos de `raw` depois que a USGS responde, para a execução não herdar arquivos de outro período
# MAGIC - conferência dos arquivos gravados
# MAGIC
# MAGIC **Resultado esperado:** no volume `/Volumes/<catalogo>/bronze/raw/`: `usgs/eventos_<inicio>_<fim>.json` (1 arquivo), `open_meteo/<evento_id>.json` (1 por sismo) e `extracao_relatorio.json` com `completo` verdadeiro.
# MAGIC
# MAGIC Atenção: a célula de extração chama as APIs e apaga os arquivos antigos de `raw`; rode-a só pelo job.

# COMMAND ----------

# DBTITLE 1,Preparar import dos módulos
import os  # consulta a pasta atual do notebook
import sys  # controla onde o Python procura pacotes
from pathlib import Path  # monta caminhos de pastas

RAIZ = Path(os.getcwd()).parent  # pasta atual do notebook é .../notebooks; a raiz do repositório é a pasta acima
SRC = RAIZ / "src"  # pasta que contém o pacote sismos_clima
print("pasta atual do notebook:", os.getcwd())  # mostra de onde o caminho foi deduzido
if not (SRC / "sismos_clima").is_dir():  # confere se a dedução apontou para o repositório
    raise RuntimeError(f"pacote não encontrado em {SRC}; cole a saída acima para ajustarmos o caminho")  # para com mensagem clara
if str(SRC) not in sys.path:  # evita duplicar o caminho se a célula rodar de novo
    sys.path.append(str(SRC))  # acrescenta src à lista de pastas de import
import sismos_clima  # confirma que o pacote é importável
print("pacote carregado de:", sismos_clima.__file__)  # mostra o arquivo carregado

# COMMAND ----------

# DBTITLE 1,Ler parâmetros
from sismos_clima.config import carregar_configuracao  # transforma variáveis em objeto de configuração

dbutils.widgets.text("data_inicio", "2026-10-01", "Data início (AAAA-MM-DD)")  # cria o campo de texto com valor padrão
dbutils.widgets.text("data_fim", "2026-10-31", "Data fim, inclusive (AAAA-MM-DD)")  # idem para o fim do período
dbutils.widgets.text("magnitude_minima", "5", "Magnitude mínima")  # idem para a magnitude
dbutils.widgets.text("catalogo", "ft03_sismos_clima", "Catálogo do Unity Catalog")  # idem para o catálogo

cfg = carregar_configuracao({  # monta a configuração a partir dos campos, sem depender de variáveis de ambiente
    "FT03_DATA_INICIO": dbutils.widgets.get("data_inicio"),  # lê o valor do campo
    "FT03_DATA_FIM": dbutils.widgets.get("data_fim"),  # lê o valor do campo
    "FT03_MAGNITUDE_MINIMA": dbutils.widgets.get("magnitude_minima"),  # lê o valor do campo
    "FT03_CATALOGO": dbutils.widgets.get("catalogo"),  # lê o valor do campo
})
print(cfg)  # mostra a configuração que será usada

# COMMAND ----------

# DBTITLE 1,Executar extração
import json  # formata o relatório para leitura
from sismos_clima.extract import extrair  # função que baixa e grava os arquivos brutos
from sismos_clima.http_client import ClienteHttp, LimitadorTaxa  # cliente com taxa e retentativas

usgs = ClienteHttp(LimitadorTaxa(1.0))  # 1 segundo entre chamadas à USGS (valor conservador, limite não publicado)
meteo = ClienteHttp(LimitadorTaxa(0.5))  # 0,5 segundo entre chamadas ao Open-Meteo (120 por minuto, limite é 600)
pasta_raw = Path(f"/Volumes/{cfg.catalogo}/bronze/raw")  # volume gerenciado criado na etapa de ambiente
relatorio = extrair(cfg, usgs, meteo, pasta_raw)  # 1 count + 1 query + 1 chamada de clima por sismo
print(json.dumps(relatorio, indent=2, ensure_ascii=False))  # mostra o relatório da extração

# COMMAND ----------

# DBTITLE 1,Conferir arquivos gravados
pasta_clima = pasta_raw / "open_meteo"  # pasta com um arquivo de clima por sismo
pasta_usgs = pasta_raw / "usgs"  # pasta com o GeoJSON dos sismos
print("arquivos de clima:", len(os.listdir(pasta_clima)))  # deve ser igual a count_usgs quando completo
print("arquivos da USGS:", os.listdir(pasta_usgs))  # deve listar o arquivo do período
print("extração completa:", relatorio["completo"])  # True quando tudo o que a USGS contou foi baixado
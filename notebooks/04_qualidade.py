# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Preparar import dos módulos
import os  # consulta a pasta atual do notebook
import sys  # controla onde o Python procura pacotes
from pathlib import Path  # monta caminhos de pastas

RAIZ = Path(os.getcwd()).parent  # pasta atual do notebook é .../notebooks; a raiz do repositório é a pasta acima
SRC = RAIZ / "src"  # pasta que contém o pacote sismos_clima
if not (SRC / "sismos_clima").is_dir():  # confere se a dedução apontou para o repositório
    raise RuntimeError(f"pacote não encontrado em {SRC}")  # para com mensagem clara
if str(SRC) not in sys.path:  # evita duplicar o caminho se a célula rodar de novo
    sys.path.append(str(SRC))  # acrescenta src à lista de pastas de import
import sismos_clima.quality  # confirma que o módulo de qualidade é importável
print("módulo carregado de:", sismos_clima.quality.__file__)  # mostra o arquivo carregado

# COMMAND ----------

# DBTITLE 1,Ler parâmetros
from datetime import datetime, timezone  # marca o início da execução em UTC
from sismos_clima.config import carregar_configuracao  # transforma variáveis em objeto de configuração

iniciado_em = datetime.now(timezone.utc)  # instante em que a verificação começou
dbutils.widgets.text("data_inicio", "2026-10-01", "Data início (AAAA-MM-DD)")  # cria o campo de texto com valor padrão
dbutils.widgets.text("data_fim", "2026-10-31", "Data fim, inclusive (AAAA-MM-DD)")  # idem para o fim do período
dbutils.widgets.text("magnitude_minima", "5", "Magnitude mínima")  # idem para a magnitude
dbutils.widgets.text("catalogo", "ft03_sismos_clima", "Catálogo do Unity Catalog")  # idem para o catálogo

cfg = carregar_configuracao({  # monta a configuração a partir dos campos
    "FT03_DATA_INICIO": dbutils.widgets.get("data_inicio"),  # lê o valor do campo
    "FT03_DATA_FIM": dbutils.widgets.get("data_fim"),  # lê o valor do campo
    "FT03_MAGNITUDE_MINIMA": dbutils.widgets.get("magnitude_minima"),  # lê o valor do campo
    "FT03_CATALOGO": dbutils.widgets.get("catalogo"),  # lê o valor do campo
})
print(cfg)  # mostra a configuração que será usada

# COMMAND ----------

# DBTITLE 1,Ler as regras calculadas em SQL
from sismos_clima.quality import resultado_de_linha  # converte uma linha da tabela em ResultadoRegra

linhas_sql = spark.table(f"{cfg.catalogo}.gold.qualidade_regras").collect()  # tabela criada por sql/quality/02_regras.sql
regras = [resultado_de_linha(linha.asDict()) for linha in linhas_sql]  # o status é recalculado no Python
print("regras vindas do SQL:", len(regras))  # esperado 10
print([r.regra_id for r in regras])  # ids lidos

# COMMAND ----------

# DBTITLE 1,Conferir os schemas (Q-01)
from sismos_clima.quality import ESQUEMAS_ESPERADOS, verificar_schema  # schemas esperados e a regra Q-01

for regra_id, (tabela, esperado) in ESQUEMAS_ESPERADOS.items():  # uma verificação por tabela
    real = dict(spark.table(f"{cfg.catalogo}.{tabela}").dtypes)  # nome -> tipo reais, só colunas
    resultado = verificar_schema(regra_id, tabela, esperado, real)  # compara com o plano
    regras.append(resultado)  # junta à lista de regras do relatório
    print(regra_id, tabela, resultado.status, resultado.detalhes)  # mostra o resultado e o que falhou

# COMMAND ----------

# DBTITLE 1,Contar registros por camada e rejeitados
import json  # lê o relatório da extração

bronze_usgs_eventos = spark.sql(f"SELECT sum(size(features)) AS n FROM {cfg.catalogo}.bronze.usgs_resposta").first()["n"] or 0  # sismos dentro dos arquivos da USGS
bronze_clima_horas = spark.sql(f"SELECT sum(size(hourly.time)) AS n FROM {cfg.catalogo}.bronze.meteo_resposta").first()["n"] or 0  # horas dentro dos arquivos do Open-Meteo
silver_sismos = spark.table(f"{cfg.catalogo}.silver.sismos").count()  # sismos na silver
silver_clima_horas = spark.table(f"{cfg.catalogo}.silver.clima_horario").count()  # horas de clima na silver
gold_linhas = spark.table(f"{cfg.catalogo}.gold.sismo_clima_horario").count()  # linhas na gold
relatorio_extracao = json.loads(Path(f"/Volumes/{cfg.catalogo}/bronze/raw/extracao_relatorio.json").read_text(encoding="utf-8"))  # gravado pela extração
count_usgs = int(relatorio_extracao["count_usgs"])  # quantidade que a USGS informou

contagens = {  # números por camada, para o relatório
    "count_usgs": count_usgs, "bronze_usgs_eventos": int(bronze_usgs_eventos), "silver_sismos": silver_sismos,
    "bronze_clima_horas": int(bronze_clima_horas), "silver_clima_horas": silver_clima_horas, "gold_linhas": gold_linhas,
}
rejeitados = {  # o que entrou na bronze e não chegou à silver (nulos ou duplicados)
    "sismos": int(bronze_usgs_eventos) - silver_sismos,
    "horas_de_clima": int(bronze_clima_horas) - silver_clima_horas,
}
print(contagens)  # mostra as contagens
print(rejeitados)  # mostra os rejeitados

# COMMAND ----------

# DBTITLE 1,Contar nulos e estatísticas do clima (Q-03)
from pyspark.sql import functions as F  # funções de agregação do Spark
from sismos_clima.quality import COLUNAS_CLIMA, taxa_nulos, verificar_contagem_usgs, verificar_nulos_clima  # regras Q-03 e Q-10

gold = spark.table(f"{cfg.catalogo}.gold.sismo_clima_horario")  # tabela final
agregados = [F.sum(F.col(c).isNull().cast("int")).alias(f"nulos_{c}") for c in COLUNAS_CLIMA]  # nulos de cada variável
agregados += [F.min(c).alias(f"min_{c}") for c in COLUNAS_CLIMA]  # menor valor de cada variável
agregados += [F.max(c).alias(f"max_{c}") for c in COLUNAS_CLIMA]  # maior valor de cada variável
agregados += [F.avg(c).alias(f"media_{c}") for c in COLUNAS_CLIMA]  # média de cada variável
linha = gold.agg(*agregados).first().asDict()  # uma única linha com tudo

nulos_clima = taxa_nulos(gold_linhas, {c: int(linha[f"nulos_{c}"] or 0) for c in COLUNAS_CLIMA})  # taxa de nulos por coluna
estatisticas_clima = {c: {"minimo": linha[f"min_{c}"], "maximo": linha[f"max_{c}"], "media": linha[f"media_{c}"]} for c in COLUNAS_CLIMA}  # só informação
regras.append(verificar_nulos_clima(nulos_clima))  # Q-03, nível aviso
regras.append(verificar_contagem_usgs(count_usgs, silver_sismos))  # Q-10, nível erro
print(nulos_clima)  # mostra os nulos por coluna

# COMMAND ----------

# DBTITLE 1,Montar e gravar o relatório
import uuid  # gera o identificador da execução
from sismos_clima.quality import gravar_relatorio, montar_relatorio  # monta e grava o JSON

relatorio = montar_relatorio(
    execucao_id=str(uuid.uuid4()),  # identificador único desta execução
    iniciado_em_utc=iniciado_em.isoformat(),  # início
    finalizado_em_utc=datetime.now(timezone.utc).isoformat(),  # fim
    periodo={"inicio": cfg.data_inicio.isoformat(), "fim": cfg.data_fim.isoformat()},  # período pedido
    magnitude_minima=cfg.magnitude_minima,  # magnitude mínima usada
    contagens=contagens, rejeitados=rejeitados,  # números por camada e rejeitados
    regras=regras, nulos_clima=nulos_clima, estatisticas_clima=estatisticas_clima,  # regras e informações
)
caminho = gravar_relatorio(relatorio, Path(f"/Volumes/{cfg.catalogo}/gold/export/reports/quality_report.json"))  # grava no volume de exportação
print("relatório gravado em:", caminho)  # mostra onde ficou
print(json.dumps(relatorio["resumo"], ensure_ascii=False), "aprovado:", relatorio["aprovado"])  # resumo
for r in relatorio["regras"]:  # lista cada regra
    print(r["regra_id"], r["status"], r["verificados"], r["violacoes"])  # id, status, verificados, violações

# COMMAND ----------

# DBTITLE 1,Aplicar a política de falha
from sismos_clima.quality import exigir_aprovacao  # levanta erro se alguma regra de erro reprovou

exigir_aprovacao(relatorio)  # o relatório já foi gravado; com regra reprovada, esta célula falha e o job para
print("qualidade aprovada: o gold pode ser exportado")  # só chega aqui se aprovado
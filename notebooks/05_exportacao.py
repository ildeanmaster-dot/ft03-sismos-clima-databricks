# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# DBTITLE 1,Ler parâmetros
dbutils.widgets.text("catalogo", "ft03_sismos_clima", "Catálogo do Unity Catalog")  # cria o campo com valor padrão; no job, o parâmetro catalogo sobrescreve
catalogo = dbutils.widgets.get("catalogo")  # lê o valor do campo
tabela_gold = f"{catalogo}.gold.sismo_clima_horario"  # tabela final, criada por sql/gold/01_gold
destino = f"/Volumes/{catalogo}/gold/export/dataset"  # pasta do dataset dentro do volume de exportação
print(tabela_gold, "->", destino)  # mostra a origem e o destino

# COMMAND ----------

# DBTITLE 1,Gravar o Parquet Snappy particionado
gold = spark.table(tabela_gold)  # lê a tabela gold (Delta) como DataFrame
linhas_gold = gold.count()  # quantidade de linhas da gold, para comparar depois
(
    gold.write  # começa a montar a gravação
    .mode("overwrite")  # substitui o dataset inteiro: reexecutar não duplica
    .partitionBy("ano", "mes")  # uma pasta por ano e mês (ano=AAAA/mes=M)
    .option("compression", "snappy")  # declara Snappy, sem depender do padrão da sessão
    .parquet(destino)  # grava em Parquet na pasta do volume
)  # fim da gravação
print("linhas na gold:", linhas_gold)  # esperado 5376 para out/2026

# COMMAND ----------

# DBTITLE 1,Listar os arquivos gravados
from pathlib import Path  # caminhos de arquivo; o volume aparece como pasta local

arquivos = sorted(Path(destino).rglob("*.parquet"))  # todos os .parquet dentro das pastas de partição
for arquivo in arquivos:  # um arquivo por linha
    print(arquivo.relative_to(destino), arquivo.stat().st_size, "bytes")  # partição, nome e tamanho
outros = sorted(str(p.relative_to(destino)) for p in Path(destino).rglob("*") if p.is_file() and p.suffix != ".parquet")  # arquivos que não são dados
print("arquivos .parquet:", len(arquivos))  # quantidade de arquivos de dados
print("outros arquivos:", outros)  # arquivos de controle que o Spark grava junto

# COMMAND ----------

# DBTITLE 1,Ler de volta e comparar com a gold
lido = spark.read.parquet(destino)  # lê o dataset exportado; ano e mes voltam pelos nomes das pastas
linhas_lidas = lido.count()  # linhas no Parquet
print("linhas lidas:", linhas_lidas, "colunas:", len(lido.columns))  # esperado 5376 linhas e 22 colunas
if linhas_lidas != linhas_gold:  # o export tem de ter as mesmas linhas da gold
    raise RuntimeError(f"Parquet com {linhas_lidas} linhas, gold com {linhas_gold}")  # para com mensagem clara
print("contagem confere com a gold")  # só chega aqui se for igual

# COMMAND ----------

# DBTITLE 1,Provar o Snappy no rodapé do Parquet
import pyarrow.parquet as pq  # lê os metadados gravados no rodapé de arquivos Parquet

codecs = set()  # compressões encontradas em todas as colunas de todos os arquivos
for arquivo in arquivos:  # cada arquivo de dados
    meta = pq.ParquetFile(str(arquivo)).metadata  # rodapé do arquivo
    for i in range(meta.num_row_groups):  # cada grupo de linhas (row group)
        grupo = meta.row_group(i)  # metadados do grupo
        for j in range(grupo.num_columns):  # cada coluna do grupo
            codecs.add(grupo.column(j).compression)  # compressão registrada para a coluna
    print(arquivo.name, "| linhas:", meta.num_rows, "| colunas:", meta.num_columns, "| formato:", meta.format_version, "| criado por:", meta.created_by)  # resumo do rodapé
print("compressões no rodapé:", codecs)  # esperado {'SNAPPY'}
if codecs != {"SNAPPY"}:  # qualquer outra compressão viola o requisito
    raise RuntimeError(f"compressão diferente de Snappy: {codecs}")  # para com mensagem clara
print("Snappy confirmado no rodapé de", len(arquivos), "arquivo(s)")  # só chega aqui se tudo for Snappy
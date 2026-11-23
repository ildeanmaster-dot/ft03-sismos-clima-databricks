# Databricks notebook source
# DBTITLE 1,1 - Contar sismos (USGS count)
import requests  # biblioteca HTTP do Python: é ela que faz a chamada GET para a API

USGS = "https://earthquake.usgs.gov/fdsnws/event/1"  # endereço base do serviço de eventos da USGS
PERIODO = {  # dicionário com os filtros reaproveitados nas próximas células
    "starttime": "2026-10-01",  # início do período, em UTC
    "endtime": "2026-11-01",  # fim do período: 01/11 às 00:00 UTC fecha outubro inteiro
    "minmagnitude": 5,  # só terremotos de magnitude 5 ou mais
}

resposta = requests.get(  # executa a chamada GET e guarda a resposta
    f"{USGS}/count",  # método count: devolve só a quantidade
    params={**PERIODO, "format": "geojson"},  # junta os filtros com o formato da resposta
    timeout=(10, 30),  # até 10 s para conectar e 30 s para receber
)
print(resposta.status_code)  # 200 = sucesso
print(resposta.url)  # URL completa montada pelo requests
print(resposta.json())  # corpo da resposta como dicionário

# COMMAND ----------

# DBTITLE 1,2 - Buscar 3 sismos (USGS query)
import json  # formata JSON de forma legível

resposta = requests.get(  # nova chamada GET, agora no método query
    f"{USGS}/query",  # método query: devolve os eventos
    params={**PERIODO, "format": "geojson", "orderby": "time-asc", "limit": 3},  # mesmos filtros, ordem fixa, só 3 eventos
    timeout=(10, 30),  # mesmos tempos limite
)
resposta.raise_for_status()  # lança erro se o status for 4xx ou 5xx
geo = resposta.json()  # corpo da resposta como dicionário
print(resposta.status_code, "| features:", len(geo["features"]))  # status e quantidade de eventos
print(list(geo.keys()))  # chaves do nível de cima do GeoJSON
print(json.dumps(geo["features"][0], indent=2)[:1800])  # primeiro evento formatado

# COMMAND ----------

# DBTITLE 1,3 - Clima do epicentro (Open-Meteo)
import datetime as dt  # datas e horas

METEO = "https://archive-api.open-meteo.com/v1/archive"  # endpoint do histórico da Open-Meteo
VARIAVEIS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "surface_pressure"]  # 5 variáveis horárias

evento = geo["features"][0]  # primeiro sismo
lon, lat, prof = evento["geometry"]["coordinates"]  # longitude vem ANTES da latitude
instante = dt.datetime.fromtimestamp(evento["properties"]["time"] / 1000, tz=dt.timezone.utc)  # ms -> data e hora UTC
dia = instante.date().isoformat()  # data AAAA-MM-DD
print("evento:", evento["id"], "| UTC:", instante, "| dia pedido:", dia)  # confere a conversão

resposta = requests.get(  # chamada GET ao Open-Meteo
    METEO,
    params={"latitude": lat, "longitude": lon, "start_date": dia, "end_date": dia,  # ponto e dia do evento
            "hourly": ",".join(VARIAVEIS), "timezone": "GMT"},  # variáveis e fuso UTC
    timeout=(10, 30),
)
print(resposta.status_code, resposta.url[:120])  # status e início da URL
resposta.raise_for_status()  # para se vier erro
clima = resposta.json()  # resposta como dicionário

print("enviado  :", lat, lon)  # coordenada enviada
print("devolvido:", clima["latitude"], clima["longitude"], "| elevação:", clima.get("elevation"))  # coordenada usada pela API
print("unidades :", clima["hourly_units"])  # unidade de cada variável
print("chaves de hourly:", list(clima["hourly"].keys()))  # listas paralelas
print("horas:", len(clima["hourly"]["time"]), "| de", clima["hourly"]["time"][0], "até", clima["hourly"]["time"][-1])  # tamanho e extremos
for nome in VARIAVEIS:  # percorre cada variável
    lista = clima["hourly"][nome]  # 24 valores
    print(nome, "| nulos:", sum(v is None for v in lista), "| primeiros 3:", lista[:3])  # nulos e amostra

# COMMAND ----------

# DBTITLE 1,4 - Clima dos 3 sismos (fecha a Etapa 0)
import time  # time.sleep dá pausa entre chamadas

resumo = []  # resultado de cada sismo
for evento in geo["features"]:  # percorre os 3 sismos
    props = evento["properties"]  # propriedades do evento
    lon, lat, prof = evento["geometry"]["coordinates"]  # longitude antes da latitude
    instante = dt.datetime.fromtimestamp(props["time"] / 1000, tz=dt.timezone.utc)  # ms -> UTC
    dia = instante.date().isoformat()  # data AAAA-MM-DD
    r = requests.get(  # chamada ao Open-Meteo
        METEO,
        params={"latitude": lat, "longitude": lon, "start_date": dia, "end_date": dia,
                "hourly": ",".join(VARIAVEIS), "timezone": "GMT"},
        timeout=(10, 30),
    )
    r.raise_for_status()  # interrompe se vier erro
    h = r.json()["hourly"]  # listas horárias
    nulos = sum(v is None for nome in VARIAVEIS for v in h[nome])  # nulos nas 5 variáveis
    resumo.append({"id": evento["id"], "mag": props["mag"], "lugar": props["place"],  # identificação do sismo
                   "utc": instante.strftime("%Y-%m-%d %H:%M"), "horas_clima": len(h["time"]), "nulos": nulos})  # hora e checagens
    time.sleep(1)  # espaçamento simples de teste; o controle definitivo fica no http_client

for linha in resumo:  # imprime o resumo
    print(linha)
print("sismos com 24 horas de clima:", sum(l["horas_clima"] == 24 for l in resumo), "de", len(resumo))  # fechamento da Etapa 0

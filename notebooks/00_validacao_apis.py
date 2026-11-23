# Databricks notebook source
# Etapa 0 — validação das duas APIs no Databricks Free Edition (serverless)
# Consulta 3 terremotos M5+ de outubro/2026 (USGS) e o clima horário do epicentro no dia UTC do evento (Open-Meteo).
# Resultado esperado: 24 horas de clima por terremoto.
import datetime as dt
import time
from typing import Any

import requests

USGS = "https://earthquake.usgs.gov/fdsnws/event/1"
METEO = "https://archive-api.open-meteo.com/v1/archive"
HOURLY = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "surface_pressure"]
PERIODO = {"starttime": "2026-10-01", "endtime": "2026-11-01", "minmagnitude": 5}
TIMEOUT = (10, 30)


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    r = requests.get(url, params=params, timeout=TIMEOUT)
    print(f"{r.status_code} {r.url[:110]}")
    r.raise_for_status()
    return r.json()


# 1) Quantos eventos M5+ existem no mês (método count da USGS)
contagem = get_json(f"{USGS}/count", {**PERIODO, "format": "geojson"})
print("USGS count out/2026 M5+:", contagem)

# 2) Três primeiros eventos do mês
geo = get_json(f"{USGS}/query", {**PERIODO, "format": "geojson", "orderby": "time-asc", "limit": 3})
print("features recebidas:", len(geo["features"]))

# 3) Clima do epicentro no dia UTC de cada evento
for f in geo["features"]:
    p = f["properties"]
    lon, lat, prof = f["geometry"]["coordinates"]
    quando = dt.datetime.fromtimestamp(p["time"] / 1000, tz=dt.timezone.utc)
    dia = quando.date().isoformat()
    clima = get_json(METEO, {"latitude": lat, "longitude": lon, "start_date": dia, "end_date": dia,
                             "hourly": ",".join(HOURLY), "timezone": "GMT"})
    h = clima["hourly"]
    nulos = {v: sum(x is None for x in h[v]) for v in HOURLY}
    print(f"\n{f['id']} | M{p['mag']} {p['magType']} | {p['place']} | {quando:%Y-%m-%d %H:%M:%S}Z")
    print(f"  epicentro lat={lat} lon={lon} prof={prof} km | grade Open-Meteo lat={clima['latitude']} lon={clima['longitude']} elev={clima.get('elevation')}")
    print(f"  horas={len(h['time'])} ({h['time'][0]} .. {h['time'][-1]}) | nulos={nulos}")
    time.sleep(1)  # espaçamento simples; o controle de taxa definitivo fica no cliente HTTP do pipeline

"""Extração da USGS (GeoJSON) e do Open-Meteo (horário) para o volume bronze.

Esta parte reúne as funções puras, sem rede nem arquivos: montam os parâmetros das
chamadas a partir da configuração e de um evento. A gravação no volume vem depois.
"""
from __future__ import annotations  # permite anotações de tipo modernas em Python 3.9+

from datetime import date, datetime, timezone  # datas e fuso UTC
from typing import Any, Dict, Mapping, Optional  # tipos usados nas anotações

from sismos_clima.config import Configuracao  # parâmetros do pipeline

USGS_BASE = "https://earthquake.usgs.gov/fdsnws/event/1"  # endereço base do serviço de eventos
METEO_URL = "https://archive-api.open-meteo.com/v1/archive"  # endpoint do histórico do Open-Meteo
VARIAVEIS_HORARIAS = (  # as 5 variáveis horárias pedidas (menos de 10: conta como 1 chamada)
    "temperature_2m",  # temperatura a 2 m, em °C
    "relative_humidity_2m",  # umidade relativa a 2 m, em %
    "precipitation",  # precipitação, em mm
    "wind_speed_10m",  # velocidade do vento a 10 m, em km/h
    "surface_pressure",  # pressão na superfície, em hPa
)


def filtros_usgs(config: Configuracao) -> Dict[str, Any]:
    """Filtros comuns às chamadas `count` e `query` da USGS."""
    return {
        "format": "geojson",  # formato da resposta
        "starttime": config.data_inicio.isoformat(),  # início inclusivo, AAAA-MM-DD
        "endtime": config.data_fim_exclusiva.isoformat(),  # dia seguinte ao fim (ver A9)
        "minmagnitude": config.magnitude_minima,  # magnitude mínima
    }


def parametros_query_usgs(config: Configuracao, limite: Optional[int] = None) -> Dict[str, Any]:
    """Parâmetros do método `query`: os filtros mais a ordem fixa e, se pedido, o limite."""
    parametros = {**filtros_usgs(config), "orderby": "time-asc"}  # ordem estável entre execuções
    if limite is not None:  # sem limite, a USGS devolve até 20000 eventos
        parametros["limit"] = limite  # limite pedido (útil para testes)
    return parametros  # dicionário pronto para o requests


def dia_utc(evento: Mapping[str, Any]) -> date:
    """Dia UTC do sismo (decisão P-03: o clima é do dia UTC em que o sismo ocorreu)."""
    milissegundos = evento["properties"]["time"]  # `time` vem em ms desde 1970, em UTC
    return datetime.fromtimestamp(milissegundos / 1000, tz=timezone.utc).date()  # converte e fica só com o dia


def parametros_meteo(evento: Mapping[str, Any]) -> Dict[str, Any]:
    """Parâmetros da chamada ao Open-Meteo para o epicentro e o dia UTC do sismo."""
    longitude, latitude = evento["geometry"]["coordinates"][:2]  # no GeoJSON a longitude vem antes da latitude
    dia = dia_utc(evento).isoformat()  # AAAA-MM-DD
    return {
        "latitude": latitude,  # latitude do epicentro
        "longitude": longitude,  # longitude do epicentro
        "start_date": dia,  # um dia só
        "end_date": dia,  # mesmo dia: 24 horas
        "hourly": ",".join(VARIAVEIS_HORARIAS),  # variáveis separadas por vírgula
        "timezone": "GMT",  # horas em UTC (00:00 a 23:00)
    }

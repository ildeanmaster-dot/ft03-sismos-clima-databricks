"""Testes das funções puras de extração."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # torna src importável

from sismos_clima.config import carregar_configuracao  # noqa: E402
from sismos_clima.extract import (  # noqa: E402
    dia_utc,
    filtros_usgs,
    parametros_meteo,
    parametros_query_usgs,
)

EVENTO = {  # recorte do evento us6000tyny da Etapa 0 (01/10/2026 01:29:20.875 UTC)
    "id": "us6000tyny",
    "properties": {"time": 1790818160875},
    "geometry": {"coordinates": [68.7436, 36.1078, 55.091]},
}


def test_filtros_usam_dia_seguinte_como_fim():
    filtros = filtros_usgs(carregar_configuracao({}))
    assert filtros["starttime"] == "2026-10-01"
    assert filtros["endtime"] == "2026-11-01"
    assert filtros["minmagnitude"] == 5.0 and filtros["format"] == "geojson"


def test_query_tem_ordem_e_limite_opcional():
    config = carregar_configuracao({})
    assert parametros_query_usgs(config)["orderby"] == "time-asc"
    assert "limit" not in parametros_query_usgs(config)
    assert parametros_query_usgs(config, limite=3)["limit"] == 3


def test_dia_utc_do_evento():
    assert dia_utc(EVENTO) == date(2026, 10, 1)


def test_dia_utc_nos_limites_do_dia():
    meia_noite = {"properties": {"time": 1790812800000}}  # 2026-10-01 00:00:00.000 UTC
    ultimo_ms = {"properties": {"time": 1790899199999}}  # 2026-10-01 23:59:59.999 UTC
    assert dia_utc(meia_noite) == date(2026, 10, 1)
    assert dia_utc(ultimo_ms) == date(2026, 10, 1)


def test_parametros_meteo_longitude_antes_da_latitude():
    p = parametros_meteo(EVENTO)
    assert p["latitude"] == 36.1078 and p["longitude"] == 68.7436
    assert p["start_date"] == p["end_date"] == "2026-10-01"
    assert p["timezone"] == "GMT"
    assert p["hourly"].split(",") == [
        "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "surface_pressure",
    ]

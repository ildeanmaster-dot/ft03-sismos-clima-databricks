"""Testes das funções puras de extração.

O que faz: confere filtros, parâmetros, dia UTC, gravação e limpeza do `raw` com dados pequenos.
Resultado esperado: 13 testes aprovados.
"""
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


# ---- extrair: gravação no volume (usa pasta temporária e clientes falsos) ----
import json  # noqa: E402

import pytest  # noqa: E402

from sismos_clima.extract import ErroExtracao, METEO_URL, extrair, limpar_raw  # noqa: E402
from sismos_clima.http_client import ErroPermanente  # noqa: E402


class ClienteFalso:
    """Responde por url; um valor Exception é levantado em vez de devolvido."""

    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    def get_json(self, url, params=None):
        self.chamadas.append((url, params))
        resposta = self.respostas[url]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _evento(id_, ms=1790818160875):
    return {"id": id_, "properties": {"time": ms}, "geometry": {"coordinates": [68.7436, 36.1078, 55.0]}}


def _usgs(total, eventos):
    return ClienteFalso({
        "https://earthquake.usgs.gov/fdsnws/event/1/count": {"count": total, "maxAllowed": 20000},
        "https://earthquake.usgs.gov/fdsnws/event/1/query": {"type": "FeatureCollection", "features": eventos},
    })


def test_extrair_grava_arquivos_e_relatorio(tmp_path):
    usgs = _usgs(2, [_evento("a1"), _evento("b2")])
    meteo = ClienteFalso({METEO_URL: {"hourly": {"time": []}}})
    relatorio = extrair(carregar_configuracao({}), usgs, meteo, tmp_path)
    assert relatorio["completo"] is True and relatorio["chamadas"] == 4
    assert (tmp_path / "usgs" / "eventos_2026-10-01_2026-10-31.json").exists()
    assert sorted(p.name for p in (tmp_path / "open_meteo").iterdir()) == ["a1.json", "b2.json"]
    assert json.loads((tmp_path / "extracao_relatorio.json").read_text())["climas_gravados"] == 2


def test_extrair_falha_de_um_clima_salva_relatorio_e_levanta(tmp_path):
    usgs = _usgs(1, [_evento("a1")])
    meteo = ClienteFalso({METEO_URL: ErroPermanente("HTTP 400")})
    with pytest.raises(ErroExtracao):
        extrair(carregar_configuracao({}), usgs, meteo, tmp_path)
    relatorio = json.loads((tmp_path / "extracao_relatorio.json").read_text())
    assert relatorio["falhas"][0]["evento_id"] == "a1" and relatorio["completo"] is False


def test_extrair_recusa_periodo_acima_do_maximo(tmp_path):
    with pytest.raises(ErroExtracao):
        extrair(carregar_configuracao({}), _usgs(20001, []), ClienteFalso({}), tmp_path)


def test_extrair_recusa_id_com_barra(tmp_path):
    usgs = _usgs(1, [_evento("../x")])
    meteo = ClienteFalso({METEO_URL: {}})
    with pytest.raises(ErroExtracao):
        extrair(carregar_configuracao({}), usgs, meteo, tmp_path)
    assert meteo.chamadas == []
    assert not (tmp_path.parent / "x.json").exists()


def test_extrair_com_limite_nao_marca_completo(tmp_path):
    usgs = _usgs(224, [_evento("a1")])
    meteo = ClienteFalso({METEO_URL: {}})
    assert extrair(carregar_configuracao({}), usgs, meteo, tmp_path, limite=1)["completo"] is False


def test_extrair_apaga_arquivos_de_periodo_anterior(tmp_path):
    (tmp_path / "usgs").mkdir()
    (tmp_path / "open_meteo").mkdir()
    (tmp_path / "_teste").mkdir()
    (tmp_path / "usgs" / "eventos_2026-09-01_2026-09-30.json").write_text("{}")
    (tmp_path / "open_meteo" / "velho.json").write_text("{}")
    (tmp_path / "_teste" / "fica.json").write_text("{}")
    usgs = _usgs(1, [_evento("a1")])
    meteo = ClienteFalso({METEO_URL: {"hourly": {"time": []}}})
    relatorio = extrair(carregar_configuracao({}), usgs, meteo, tmp_path)
    assert relatorio["arquivos_antigos_removidos"] == 2
    assert sorted(p.name for p in (tmp_path / "usgs").iterdir()) == ["eventos_2026-10-01_2026-10-31.json"]
    assert sorted(p.name for p in (tmp_path / "open_meteo").iterdir()) == ["a1.json"]
    assert (tmp_path / "_teste" / "fica.json").exists()


def test_extrair_nao_apaga_nada_se_a_usgs_falha(tmp_path):
    (tmp_path / "usgs").mkdir()
    (tmp_path / "usgs" / "eventos_antigo.json").write_text("{}")
    usgs = ClienteFalso({"https://earthquake.usgs.gov/fdsnws/event/1/count": ErroPermanente("HTTP 400")})
    with pytest.raises(ErroPermanente):
        extrair(carregar_configuracao({}), usgs, ClienteFalso({}), tmp_path)
    assert (tmp_path / "usgs" / "eventos_antigo.json").exists()


def test_limpar_raw_sem_pastas_devolve_zero(tmp_path):
    assert limpar_raw(tmp_path) == 0

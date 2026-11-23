"""Testes do cliente HTTP: sucesso, 429 com Retry-After, 5xx, timeout, erro permanente e esgotamento."""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # torna src importável

from sismos_clima.http_client import (  # noqa: E402
    ClienteHttp,
    ErroPermanente,
    ErroTentativasEsgotadas,
    LimitadorTaxa,
)


class RespostaFalsa:
    """Imita o necessário de requests.Response."""

    def __init__(self, status: int, corpo: Optional[Dict[str, Any]] = None, cabecalhos: Optional[Dict[str, str]] = None):
        self.status_code = status
        self._corpo = corpo or {}
        self.headers = cabecalhos or {}
        self.text = str(self._corpo)

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self) -> Dict[str, Any]:
        return self._corpo


class SessaoFalsa:
    """Devolve (ou levanta) os itens do roteiro, na ordem."""

    def __init__(self, roteiro: List[Any]):
        self._roteiro = list(roteiro)
        self.chamadas = 0

    def get(self, url: str, params: Any = None, timeout: Any = None) -> Any:
        self.chamadas += 1
        item = self._roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def montar(roteiro: List[Any], **kwargs: Any):
    esperas: List[float] = []
    sessao = SessaoFalsa(roteiro)
    cliente = ClienteHttp(LimitadorTaxa(0), sessao=sessao, dormir=esperas.append, sorteio=lambda: 0.0, **kwargs)
    return cliente, sessao, esperas


def test_sucesso_direto():
    cliente, sessao, esperas = montar([RespostaFalsa(200, {"a": 1})])
    assert cliente.get_json("https://x.test") == {"a": 1}
    assert sessao.chamadas == 1 and esperas == []


def test_429_respeita_retry_after():
    cliente, _, esperas = montar([RespostaFalsa(429, cabecalhos={"Retry-After": "3"}), RespostaFalsa(200, {"ok": 1})])
    assert cliente.get_json("https://x.test") == {"ok": 1}
    assert esperas == [3.0]


def test_5xx_usa_backoff_exponencial_com_teto():
    cliente, _, esperas = montar([RespostaFalsa(503)] * 5 + [RespostaFalsa(200, {"ok": 1})])
    cliente.get_json("https://x.test")
    assert esperas == [1.0, 2.0, 4.0, 8.0, 8.0]


def test_timeout_e_retentado():
    cliente, sessao, esperas = montar([requests.Timeout("lento"), RespostaFalsa(200, {"ok": 1})])
    assert cliente.get_json("https://x.test") == {"ok": 1}
    assert sessao.chamadas == 2 and esperas == [1.0]


def test_erro_permanente_nao_repete():
    cliente, sessao, esperas = montar([RespostaFalsa(400, {"reason": "ruim"})])
    with pytest.raises(ErroPermanente):
        cliente.get_json("https://x.test")
    assert sessao.chamadas == 1 and esperas == []


def test_esgota_tentativas():
    cliente, sessao, _ = montar([RespostaFalsa(500)] * 6)
    with pytest.raises(ErroTentativasEsgotadas):
        cliente.get_json("https://x.test")
    assert sessao.chamadas == 6


def test_retry_after_muito_longo_desiste():
    cliente, sessao, esperas = montar([RespostaFalsa(429, cabecalhos={"Retry-After": "600"})])
    with pytest.raises(ErroTentativasEsgotadas):
        cliente.get_json("https://x.test")
    assert sessao.chamadas == 1 and esperas == []


def test_limitador_espera_so_o_que_falta():
    tempo = [0.0]
    esperas: List[float] = []

    def dormir(s: float) -> None:
        esperas.append(s)
        tempo[0] += s

    limitador = LimitadorTaxa(1.0, relogio=lambda: tempo[0], dormir=dormir)
    assert limitador.aguardar() == 0.0
    tempo[0] += 0.6
    assert round(limitador.aguardar(), 2) == 0.4
    assert esperas == [pytest.approx(0.4)]

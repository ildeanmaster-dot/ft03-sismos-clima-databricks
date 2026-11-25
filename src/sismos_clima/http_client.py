"""Cliente HTTP único com controle de taxa e retentativas (429, 5xx, timeout).

O que faz: centraliza toda chamada HTTP do pipeline.
O que contém: `LimitadorTaxa`, as exceções `ErroHttp`, `ErroPermanente` e `ErroTentativasEsgotadas`, e `ClienteHttp.get_json`.
Resultado esperado: `get_json` devolve o JSON da resposta; erro transitório é repetido com espera crescente e jitter; erro permanente (como 400) falha na hora; esgotadas as tentativas, levanta `ErroTentativasEsgotadas`.

Controle de taxa (LimitadorTaxa) e retentativa são tarefas distintas: o primeiro evita
chamar rápido demais; a segunda trata falhas que acontecem mesmo assim.
"""
from __future__ import annotations  # permite anotações de tipo modernas em Python 3.9+

import logging  # registra avisos de retentativa sem usar print
import random  # sorteia o jitter (variação aleatória) da espera
import time  # time.monotonic mede intervalos; time.sleep pausa a execução
from typing import Any, Callable, Mapping, Optional, Tuple  # tipos usados nas anotações

import requests  # biblioteca HTTP; já vem instalada no Databricks serverless

logger = logging.getLogger(__name__)  # logger deste módulo; nunca recebe credenciais

STATUS_TRANSITORIOS = frozenset({429, 500, 502, 503, 504})  # códigos que valem nova tentativa


class LimitadorTaxa:
    """Garante um intervalo mínimo entre duas chamadas consecutivas a uma mesma API."""

    def __init__(
        self,
        intervalo_minimo_s: float,  # segundos mínimos entre o início de duas chamadas
        relogio: Callable[[], float] = time.monotonic,  # função que devolve "agora" em segundos
        dormir: Callable[[float], None] = time.sleep,  # função que pausa por N segundos
    ) -> None:
        if intervalo_minimo_s < 0:  # intervalo negativo não faz sentido
            raise ValueError("intervalo_minimo_s não pode ser negativo")
        self._intervalo = intervalo_minimo_s  # guarda o intervalo configurado
        self._relogio = relogio  # guarda o relógio (trocável nos testes)
        self._dormir = dormir  # guarda a função de pausa (trocável nos testes)
        self._ultimo: Optional[float] = None  # instante da última chamada; None antes da primeira

    def aguardar(self) -> float:
        """Pausa o necessário para respeitar o intervalo e devolve quantos segundos esperou."""
        esperou = 0.0  # começa assumindo que não precisa esperar
        if self._ultimo is not None:  # a primeira chamada nunca espera
            falta = self._intervalo - (self._relogio() - self._ultimo)  # quanto ainda falta do intervalo
            if falta > 0:  # só espera se o intervalo ainda não passou
                self._dormir(falta)  # pausa pelo tempo que falta
                esperou = falta  # registra a espera
        self._ultimo = self._relogio()  # marca o instante desta chamada para a próxima
        return esperou  # devolve a espera, útil para log e testes


class ErroHttp(Exception):
    """Base dos erros deste cliente."""


class ErroPermanente(ErroHttp):
    """Resposta de erro que não adianta repetir (ex.: 400, 404)."""


class ErroTentativasEsgotadas(ErroHttp):
    """Falha transitória que persistiu depois de todas as retentativas."""


def _ler_retry_after(resposta: Any) -> Optional[float]:
    """Lê o cabeçalho Retry-After em segundos; devolve None se ausente ou em outro formato."""
    valor = resposta.headers.get("Retry-After")  # texto do cabeçalho, se existir
    if valor is None:  # a API não indicou espera
        return None  # usaremos o backoff exponencial
    try:  # o cabeçalho pode trazer segundos ou uma data HTTP
        return max(float(valor), 0.0)  # segundos inteiros ou decimais, nunca negativos
    except ValueError:  # formato de data HTTP não é tratado nesta versão
        return None  # cai no backoff exponencial


class ClienteHttp:
    """GET com JSON, controle de taxa, timeout explícito e retentativas com backoff e jitter."""

    def __init__(
        self,
        limitador: LimitadorTaxa,  # controla o intervalo entre chamadas desta API
        sessao: Optional[Any] = None,  # objeto com .get(); None cria requests.Session()
        max_retentativas: int = 5,  # retentativas depois da primeira chamada
        espera_base_s: float = 1.0,  # espera da 1ª retentativa; dobra a cada uma
        espera_maxima_s: float = 8.0,  # teto da espera por backoff
        retry_after_max_s: float = 60.0,  # acima disso, desiste em vez de esperar
        timeout: Tuple[float, float] = (10.0, 30.0),  # (conexão, leitura) em segundos
        dormir: Callable[[float], None] = time.sleep,  # função de pausa (trocável nos testes)
        sorteio: Callable[[], float] = random.random,  # devolve número entre 0 e 1 (trocável nos testes)
    ) -> None:
        self._limitador = limitador  # guarda o limitador de taxa
        self._sessao = sessao if sessao is not None else requests.Session()  # reaproveita a conexão
        self._max_retentativas = max_retentativas  # guarda o limite de retentativas
        self._espera_base = espera_base_s  # guarda a espera inicial
        self._espera_maxima = espera_maxima_s  # guarda o teto do backoff
        self._retry_after_max = retry_after_max_s  # guarda o teto aceito para Retry-After
        self._timeout = timeout  # guarda o timeout
        self._dormir = dormir  # guarda a função de pausa
        self._sorteio = sorteio  # guarda o gerador do jitter

    def _calcular_espera(self, numero: int, retry_after: Optional[float], url: str) -> float:
        """Define quanto esperar antes da retentativa de número `numero` (1, 2, 3...)."""
        if retry_after is not None:  # a API disse quanto esperar: obedecemos
            if retry_after > self._retry_after_max:  # espera longa demais para um job
                raise ErroTentativasEsgotadas(f"{url}: Retry-After de {retry_after:.0f}s excede {self._retry_after_max:.0f}s")
            return retry_after  # usa exatamente o valor indicado
        base = min(self._espera_base * 2 ** (numero - 1), self._espera_maxima)  # 1, 2, 4, 8, 8...
        return base + base * 0.25 * self._sorteio()  # soma até 25% de jitter para dessincronizar

    def get_json(self, url: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        """Faz GET em `url` e devolve o JSON. `url` não deve conter segredos (use `params`)."""
        total = self._max_retentativas + 1  # tentativas totais: a primeira mais as retentativas
        for tentativa in range(1, total + 1):  # tentativa 1, 2, ..., total
            self._limitador.aguardar()  # respeita o intervalo mínimo antes de cada chamada
            retry_after: Optional[float] = None  # zera o Retry-After desta tentativa
            try:  # protege a chamada contra falhas de rede
                resposta = self._sessao.get(url, params=params, timeout=self._timeout)  # chamada real
            except (requests.Timeout, requests.ConnectionError) as erro:  # falhas transitórias de rede
                motivo = type(erro).__name__  # ex.: ReadTimeout, ConnectionError
            else:  # a chamada devolveu uma resposta HTTP
                if resposta.status_code in STATUS_TRANSITORIOS:  # 429, 500, 502, 503, 504
                    motivo = f"HTTP {resposta.status_code}"  # registra o código
                    retry_after = _ler_retry_after(resposta)  # lê Retry-After, se houver
                elif resposta.ok:  # qualquer 2xx ou 3xx final
                    return resposta.json()  # sucesso: devolve o JSON já convertido
                else:  # 4xx (exceto 429): repetir não resolve
                    raise ErroPermanente(f"HTTP {resposta.status_code} em {url}: {str(resposta.text)[:200]}")
            if tentativa == total:  # acabaram as tentativas
                raise ErroTentativasEsgotadas(f"{url}: {motivo} depois de {total} tentativas")
            espera = self._calcular_espera(tentativa, retry_after, url)  # decide quanto esperar
            logger.warning("%s em %s; retentativa %d de %d em %.1fs", motivo, url, tentativa, self._max_retentativas, espera)
            self._dormir(espera)  # pausa antes de tentar de novo
        raise ErroTentativasEsgotadas(url)  # inalcançável; satisfaz o verificador de tipos

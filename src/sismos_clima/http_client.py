"""Cliente HTTP único com controle de taxa e retentativas (429, 5xx, timeout).

Controle de taxa (LimitadorTaxa) e retentativa são tarefas distintas: o primeiro evita
chamar rápido demais; a segunda trata falhas que acontecem mesmo assim.
"""
from __future__ import annotations  # permite anotações de tipo modernas em Python 3.9+

import time  # time.monotonic mede intervalos; time.sleep pausa a execução
from typing import Callable, Optional  # tipos das funções injetáveis


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

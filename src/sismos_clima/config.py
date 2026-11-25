"""Parâmetros do pipeline lidos de variáveis de ambiente.

O que faz: monta a `Configuracao` (período, magnitude mínima, catálogo) e valida o período.
O que contém: a dataclass `Configuracao` (imutável) e `carregar_configuracao`.
Resultado esperado: uma `Configuracao` válida; `data_fim` anterior a `data_inicio` levanta `ValueError`, e a extração nem começa.

Os nomes e os valores padrão seguem o arquivo .env.example da raiz do repositório.
Nenhum segredo fica no código: a chave do Open-Meteo, quando existir, vem do ambiente.
"""
from __future__ import annotations  # permite anotações de tipo modernas em Python 3.9+

import os  # os.environ guarda as variáveis de ambiente do processo
from dataclasses import dataclass  # gera __init__ e __repr__ de uma classe só de dados
from datetime import date, timedelta  # date representa um dia; timedelta, uma diferença de dias
from typing import Mapping, Optional  # tipos usados nas anotações


@dataclass(frozen=True)  # frozen=True impede alterar os campos depois de criar o objeto
class Configuracao:
    """Conjunto imutável de parâmetros de uma execução do pipeline."""

    catalogo: str  # nome do catálogo do Unity Catalog (ex.: ft03_sismos_clima)
    data_inicio: date  # primeiro dia do período, inclusive
    data_fim: date  # último dia do período, inclusive
    magnitude_minima: float  # magnitude mínima dos sismos (ex.: 5.0)
    open_meteo_apikey: Optional[str]  # chave do plano pago; None no plano gratuito

    @property  # permite ler como atributo: config.data_fim_exclusiva
    def data_fim_exclusiva(self) -> date:
        """Dia seguinte ao último dia do período, para usar como limite superior (endtime)."""
        return self.data_fim + timedelta(days=1)  # 31/10 inclusive vira 01/11 exclusivo


def carregar_configuracao(ambiente: Optional[Mapping[str, str]] = None) -> Configuracao:
    """Lê os parâmetros do ambiente, aplica os padrões e valida o período.

    Args:
        ambiente: dicionário de variáveis; se None, usa os.environ (facilita testar).

    Raises:
        ValueError: se a data de fim for anterior à data de início.
    """
    env = os.environ if ambiente is None else ambiente  # escolhe a fonte das variáveis
    data_inicio = date.fromisoformat(env.get("FT03_DATA_INICIO", "2026-10-01"))  # texto AAAA-MM-DD vira date
    data_fim = date.fromisoformat(env.get("FT03_DATA_FIM", "2026-10-31"))  # idem para o fim
    if data_fim < data_inicio:  # período invertido não faz sentido
        raise ValueError(f"FT03_DATA_FIM ({data_fim}) é anterior a FT03_DATA_INICIO ({data_inicio})")
    return Configuracao(  # monta o objeto final com os tipos corretos
        catalogo=env.get("FT03_CATALOGO", "ft03_sismos_clima"),  # catálogo criado na E2
        data_inicio=data_inicio,  # já convertido para date
        data_fim=data_fim,  # já convertido para date
        magnitude_minima=float(env.get("FT03_MAGNITUDE_MINIMA", "5")),  # "5" vira 5.0
        open_meteo_apikey=env.get("OPEN_METEO_APIKEY") or None,  # string vazia vira None
    )

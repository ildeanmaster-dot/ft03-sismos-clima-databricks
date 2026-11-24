"""Extração da USGS (GeoJSON) e do Open-Meteo (horário) para o volume bronze.

Funções puras montam os parâmetros das chamadas a partir da configuração e de um evento.
`extrair` orquestra as chamadas e grava o JSON bruto na pasta `raw` do volume:
    usgs/eventos_<inicio>_<fim>.json   uma resposta GeoJSON com todos os sismos
    open_meteo/<evento_id>.json        uma resposta do Open-Meteo por sismo
    extracao_relatorio.json            números e falhas da execução
Antes de gravar, `extrair` apaga os .json antigos de `usgs/` e `open_meteo/` (ver `limpar_raw`).
"""
from __future__ import annotations  # permite anotações de tipo modernas em Python 3.9+

import json  # grava e formata os arquivos JSON
import logging  # registra o andamento sem usar print
import re  # valida o formato do id do evento
import time  # mede a duração da extração
from datetime import date, datetime, timezone  # datas e fuso UTC
from pathlib import Path  # caminhos de arquivos
from typing import Any, Callable, Dict, List, Mapping, Optional  # tipos usados nas anotações

from sismos_clima.config import Configuracao  # parâmetros do pipeline
from sismos_clima.http_client import ClienteHttp, ErroHttp  # cliente com taxa e retentativas

logger = logging.getLogger(__name__)  # logger deste módulo

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


class ErroExtracao(Exception):
    """A extração terminou com problema que precisa parar o pipeline."""


def gravar_json(dados: Any, caminho: Path) -> None:
    """Grava `dados` como JSON em `caminho`, criando as pastas que faltarem."""
    caminho.parent.mkdir(parents=True, exist_ok=True)  # cria a pasta do arquivo se não existir
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")  # sobrescreve: reexecutar não duplica


def _id_seguro(evento_id: str) -> str:
    """O id vem de fora e vira nome de arquivo: só letras, números, hífen e sublinhado."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", str(evento_id)):  # recusa barras, pontos e espaços
        raise ErroExtracao(f"id de evento inválido para nome de arquivo: {evento_id!r}")
    return str(evento_id)  # id aceito


SUBPASTAS_RAW = ("usgs", "open_meteo")  # as únicas pastas de `raw` que a extração recria a cada execução


def limpar_raw(pasta_raw: Path) -> int:
    """Apaga os .json de execuções anteriores em `usgs/` e `open_meteo/`; devolve quantos apagou.

    Sem isso, rodar outro período deixaria arquivos antigos no volume e a bronze, que lê a pasta
    inteira, misturaria períodos (DT-09). Outras pastas de `raw` (ex.: `_teste`) não são tocadas.
    """
    apagados = 0  # contador para o relatório
    for nome in SUBPASTAS_RAW:  # só as duas pastas de dados brutos
        pasta = pasta_raw / nome  # caminho da subpasta
        if not pasta.is_dir():  # primeira execução: a pasta ainda não existe
            continue  # nada a apagar
        for arquivo in pasta.glob("*.json"):  # só arquivos .json, nunca subpastas
            arquivo.unlink()  # apaga o arquivo
            apagados += 1  # conta
    return apagados  # quantidade apagada


def extrair(
    config: Configuracao,  # período, magnitude e catálogo
    cliente_usgs: ClienteHttp,  # cliente já configurado com o intervalo da USGS
    cliente_meteo: ClienteHttp,  # cliente já configurado com o intervalo do Open-Meteo
    pasta_raw: Path,  # pasta raiz de destino (ex.: /Volumes/.../bronze/raw)
    limite: Optional[int] = None,  # limite de sismos; só para testes
    relogio: Callable[[], float] = time.monotonic,  # relógio (trocável nos testes)
) -> Dict[str, Any]:
    """Conta, baixa e grava os sismos e o clima de cada um; devolve o relatório da extração.

    Falhas de clima de um sismo não interrompem os demais: ficam no relatório e, no fim,
    levantam ErroExtracao para o job falhar de forma clara.
    """
    inicio = relogio()  # marca o começo para medir a duração
    iniciado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")  # instante UTC para o relatório
    contagem = cliente_usgs.get_json(f"{USGS_BASE}/count", params=filtros_usgs(config))  # 1ª chamada: quantos sismos
    total = int(contagem["count"])  # quantidade informada pela USGS
    maximo = int(contagem.get("maxAllowed", 20000))  # máximo por consulta
    if limite is None and total > maximo:  # o período não cabe numa consulta só
        raise ErroExtracao(f"{total} sismos excedem o máximo de {maximo} por consulta; reduza o período")
    geo = cliente_usgs.get_json(f"{USGS_BASE}/query", params=parametros_query_usgs(config, limite))  # 2ª chamada: os sismos
    eventos: List[Mapping[str, Any]] = geo["features"]  # lista de sismos do GeoJSON
    removidos = limpar_raw(pasta_raw)  # só depois de a USGS responder: falha de rede não apaga o que já existe
    gravar_json(geo, pasta_raw / "usgs" / f"eventos_{config.data_inicio}_{config.data_fim}.json")  # guarda o bruto
    falhas: List[Dict[str, str]] = []  # sismos cujo clima falhou
    climas = 0  # climas gravados com sucesso
    for evento in eventos:  # uma chamada ao Open-Meteo por sismo
        evento_id = str(evento.get("id"))  # id do sismo, usado no nome do arquivo
        try:  # uma falha aqui não derruba os outros sismos
            evento_id = _id_seguro(evento_id)  # valida o id antes de usá-lo como nome
            clima = cliente_meteo.get_json(METEO_URL, params=parametros_meteo(evento))  # clima do epicentro e do dia
            gravar_json(clima, pasta_raw / "open_meteo" / f"{evento_id}.json")  # guarda o bruto
            climas += 1  # conta o sucesso
        except (ErroHttp, ErroExtracao) as erro:  # falha de HTTP ou id inválido
            falhas.append({"evento_id": evento_id, "erro": str(erro)})  # registra para o relatório
            logger.warning("clima do evento %s falhou: %s", evento_id, erro)  # avisa no log
    relatorio: Dict[str, Any] = {
        "iniciado_em_utc": iniciado_em,  # quando começou
        "duracao_s": round(relogio() - inicio, 1),  # quanto durou
        "periodo": {"inicio": str(config.data_inicio), "fim": str(config.data_fim)},  # período pedido
        "magnitude_minima": config.magnitude_minima,  # filtro de magnitude
        "count_usgs": total,  # quantidade informada pelo `count`
        "arquivos_antigos_removidos": removidos,  # .json de períodos anteriores apagados de `raw`
        "limite_teste": limite,  # None em execução normal
        "eventos_gravados": len(eventos),  # sismos recebidos e gravados
        "climas_gravados": climas,  # arquivos de clima gravados
        "chamadas": 2 + len(eventos),  # count + query + uma por sismo
        "falhas": falhas,  # lista de falhas por sismo
        "completo": limite is None and len(eventos) == total and not falhas,  # tudo o que a USGS contou foi baixado
    }
    gravar_json(relatorio, pasta_raw / "extracao_relatorio.json")  # o relatório é salvo mesmo com falhas
    if falhas:  # política de falha: relatório salvo, depois para o job
        raise ErroExtracao(f"{len(falhas)} sismo(s) sem clima; veja extracao_relatorio.json")
    return relatorio  # devolve o relatório ao chamador

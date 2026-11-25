"""Validações de qualidade: schema, nulos, contagem da USGS e relatório JSON.

O que faz: calcula as regras feitas em Python, monta e grava o relatório e aplica a política de falha.
O que contém: `ResultadoRegra`, `resultado_de_linha`, `comparar_schema`, `verificar_schema`, `taxa_nulos`, `verificar_nulos_clima`, `verificar_contagem_usgs`, `montar_relatorio`, `gravar_relatorio`, `exigir_aprovacao` e `ErroQualidade`.
Resultado esperado: `quality_report.json` gravado antes da decisão; `exigir_aprovacao` levanta `ErroQualidade` se alguma regra de nível erro estiver reprovada.

Tudo aqui é função pura: o notebook lê os dados no Spark e passa os números prontos.
Assim cada regra se testa com entradas pequenas, sem cluster.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

NIVEL_ERRO = "erro"  # regra de erro reprova a execução
NIVEL_AVISO = "aviso"  # regra de aviso só aparece no relatório

COLUNAS_CLIMA = ("temperatura_c", "umidade_pct", "precipitacao_mm", "vento_kmh", "pressao_hpa")  # variáveis da Q-03

# Schemas conferidos com DESCRIBE TABLE no workspace em 23/11/2026 (OB-22, OB-25, OB-28 e E6 parte 2)
SCHEMA_SILVER_SISMOS: Mapping[str, str] = {
    "evento_id": "string", "magnitude": "double", "tipo_magnitude": "string", "local": "string",
    "instante_utc": "timestamp", "data_utc": "date", "longitude": "double", "latitude": "double",
    "profundidade_km": "double", "status_revisao": "string", "atualizado_em": "timestamp",
    "arquivo_origem": "string",
}
SCHEMA_SILVER_CLIMA: Mapping[str, str] = {
    "evento_id": "string", "hora_utc": "timestamp", "temperatura_c": "double", "umidade_pct": "double",
    "precipitacao_mm": "double", "vento_kmh": "double", "pressao_hpa": "double",
    "latitude_grade": "double", "longitude_grade": "double", "elevacao_m": "double",
}
SCHEMA_GOLD: Mapping[str, str] = {
    "evento_id": "string", "local": "string", "ano": "int", "mes": "int", "data_utc": "date",
    "instante_sismo_utc": "timestamp", "magnitude": "double", "latitude": "double", "longitude": "double",
    "profundidade_km": "double", "hora_utc": "timestamp", "temperatura_c": "double",
    "umidade_pct": "double", "precipitacao_mm": "double", "vento_kmh": "double", "pressao_hpa": "double",
    "faixa_magnitude": "string", "horas_desde_sismo": "int", "periodo": "string",
    "temp_media_dia_c": "double", "amplitude_termica_dia_c": "double", "precipitacao_total_dia_mm": "double",
}
# Q-01: um id por tabela, para o relatório mostrar qual tabela falhou
ESQUEMAS_ESPERADOS: Mapping[str, tuple[str, Mapping[str, str]]] = {
    "Q-01a": ("silver.sismos", SCHEMA_SILVER_SISMOS),
    "Q-01b": ("silver.clima_horario", SCHEMA_SILVER_CLIMA),
    "Q-01c": ("gold.sismo_clima_horario", SCHEMA_GOLD),
}


class ErroQualidade(Exception):
    """Pelo menos uma regra de nível erro reprovou."""


@dataclass(frozen=True)
class ResultadoRegra:
    """Resultado de uma regra: quantos registros foram verificados e quantos violam."""

    regra_id: str
    descricao: str
    tipo: str
    nivel: str
    verificados: int
    violacoes: int
    detalhes: tuple[str, ...] = ()  # o que exatamente falhou, quando a regra sabe dizer

    @property
    def status(self) -> str:
        """aprovada se não há violação; senão reprovada (erro) ou aviso."""
        if self.violacoes == 0:
            return "aprovada"
        return "reprovada" if self.nivel == NIVEL_ERRO else "aviso"

    def para_dict(self) -> dict[str, Any]:
        """Forma gravada no relatório JSON."""
        return {
            "regra_id": self.regra_id, "descricao": self.descricao, "tipo": self.tipo, "nivel": self.nivel,
            "verificados": self.verificados, "violacoes": self.violacoes, "status": self.status,
            "detalhes": list(self.detalhes),
        }


def resultado_de_linha(linha: Mapping[str, Any]) -> ResultadoRegra:
    """Converte uma linha de `gold.qualidade_regras` (Row.asDict()) em ResultadoRegra."""
    return ResultadoRegra(
        regra_id=str(linha["regra_id"]), descricao=str(linha["descricao"]), tipo=str(linha["tipo"]),
        nivel=str(linha["nivel"]), verificados=int(linha["verificados"]), violacoes=int(linha["violacoes"]),
    )  # o status é recalculado: não se confia no texto gravado na tabela


def comparar_schema(esperado: Mapping[str, str], real: Mapping[str, str]) -> list[str]:
    """Lista o que difere entre o schema esperado e o real (nome da coluna exato, tipo sem diferenciar caixa)."""
    problemas: list[str] = []
    for coluna, tipo in esperado.items():
        if coluna not in real:
            problemas.append(f"coluna ausente: {coluna}")
        elif real[coluna].lower() != tipo.lower():
            problemas.append(f"tipo diferente em {coluna}: esperado {tipo}, real {real[coluna]}")
    for coluna in real:
        if coluna not in esperado:
            problemas.append(f"coluna inesperada: {coluna}")
    return problemas


def verificar_schema(regra_id: str, tabela: str, esperado: Mapping[str, str], real: Mapping[str, str]) -> ResultadoRegra:
    """Q-01: colunas e tipos da tabela iguais ao schema do plano."""
    problemas = comparar_schema(esperado, real)
    return ResultadoRegra(
        regra_id=regra_id, descricao=f"Colunas e tipos de {tabela} iguais ao schema do plano",
        tipo="schema", nivel=NIVEL_ERRO, verificados=len(esperado), violacoes=len(problemas),
        detalhes=tuple(problemas),
    )


def taxa_nulos(total: int, nulos_por_coluna: Mapping[str, int]) -> list[dict[str, Any]]:
    """Null ratio por coluna: nulos divididos pelo total (0.0 quando a tabela está vazia)."""
    return [
        {"coluna": coluna, "nulos": int(nulos), "total": int(total),
         "taxa": (nulos / total) if total else 0.0}
        for coluna, nulos in nulos_por_coluna.items()
    ]


def verificar_nulos_clima(nulos: Sequence[Mapping[str, Any]]) -> ResultadoRegra:
    """Q-03: aviso quando alguma variável climática tem nulo (a variável nula não é preenchida, ver T2)."""
    com_nulo = [item for item in nulos if item["nulos"] > 0]
    return ResultadoRegra(
        regra_id="Q-03", descricao="Variáveis climáticas sem nulos na gold (taxa por coluna no relatório)",
        tipo="null ratio", nivel=NIVEL_AVISO, verificados=len(nulos), violacoes=len(com_nulo),
        detalhes=tuple(f"{item['coluna']}: {item['nulos']} nulos" for item in com_nulo),
    )


def verificar_contagem_usgs(count_usgs: int, sismos_silver: int) -> ResultadoRegra:
    """Q-10: sismos na silver iguais ao `count` informado pela USGS na extração."""
    diferenca = abs(count_usgs - sismos_silver)
    detalhes = (f"USGS informou {count_usgs}, silver tem {sismos_silver}",) if diferenca else ()
    return ResultadoRegra(
        regra_id="Q-10", descricao="Sismos na silver iguais ao count da USGS", tipo="completude",
        nivel=NIVEL_ERRO, verificados=count_usgs, violacoes=diferenca, detalhes=detalhes,
    )


def montar_relatorio(
    *,
    execucao_id: str,
    iniciado_em_utc: str,
    finalizado_em_utc: str,
    periodo: Mapping[str, str],
    magnitude_minima: float,
    contagens: Mapping[str, int],
    rejeitados: Mapping[str, int],
    regras: Sequence[ResultadoRegra],
    nulos_clima: Sequence[Mapping[str, Any]],
    estatisticas_clima: Mapping[str, Mapping[str, float]],
) -> dict[str, Any]:
    """Junta tudo no relatório JSON. `aprovado` só é falso quando uma regra de erro reprova."""
    ordenadas = sorted(regras, key=lambda r: r.regra_id)
    return {
        "execucao_id": execucao_id,
        "iniciado_em_utc": iniciado_em_utc,
        "finalizado_em_utc": finalizado_em_utc,
        "periodo": dict(periodo),
        "magnitude_minima": magnitude_minima,
        "contagens": dict(contagens),
        "rejeitados": dict(rejeitados),
        "resumo": {
            "regras": len(ordenadas),
            "aprovadas": sum(r.status == "aprovada" for r in ordenadas),
            "reprovadas": sum(r.status == "reprovada" for r in ordenadas),
            "avisos": sum(r.status == "aviso" for r in ordenadas),
        },
        "aprovado": all(r.status != "reprovada" for r in ordenadas),
        "regras": [r.para_dict() for r in ordenadas],
        "nulos_clima": [dict(item) for item in nulos_clima],
        "estatisticas_clima": {k: dict(v) for k, v in estatisticas_clima.items()},  # só informação, sem regra
    }


def gravar_relatorio(relatorio: Mapping[str, Any], caminho: Path) -> Path:
    """Grava o relatório em JSON legível, criando as pastas; reexecutar sobrescreve o mesmo arquivo."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def exigir_aprovacao(relatorio: Mapping[str, Any]) -> None:
    """Política de falha: com regra de erro reprovada levanta ErroQualidade (o relatório já foi gravado)."""
    if relatorio["aprovado"]:
        return
    reprovadas = [r["regra_id"] for r in relatorio["regras"] if r["status"] == "reprovada"]
    raise ErroQualidade("regras reprovadas: " + ", ".join(reprovadas))

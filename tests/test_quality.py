"""Testes das regras e do relatório de qualidade (funções puras, sem Spark)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # torna src importável

from sismos_clima.quality import (  # noqa: E402
    ErroQualidade,
    ResultadoRegra,
    comparar_schema,
    exigir_aprovacao,
    gravar_relatorio,
    montar_relatorio,
    resultado_de_linha,
    taxa_nulos,
    verificar_contagem_usgs,
    verificar_nulos_clima,
    verificar_schema,
)

ESPERADO = {"evento_id": "string", "magnitude": "double"}


def regra(nivel: str = "erro", violacoes: int = 0, regra_id: str = "Q-99") -> ResultadoRegra:
    return ResultadoRegra(regra_id, "teste", "tipo", nivel, 10, violacoes)


def relatorio(regras):
    return montar_relatorio(
        execucao_id="x", iniciado_em_utc="2026-11-23T10:00:00Z", finalizado_em_utc="2026-11-23T10:01:00Z",
        periodo={"inicio": "2026-10-01", "fim": "2026-10-31"}, magnitude_minima=5.0,
        contagens={"gold": 5376}, rejeitados={"usgs": 0}, regras=regras, nulos_clima=[], estatisticas_clima={},
    )


def test_schema_igual_nao_tem_problema():
    assert comparar_schema(ESPERADO, {"evento_id": "string", "magnitude": "double"}) == []


def test_schema_aponta_ausente_tipo_e_extra():
    problemas = comparar_schema(ESPERADO, {"evento_id": "int", "extra": "string"})
    assert "coluna ausente: magnitude" in problemas
    assert "tipo diferente em evento_id: esperado string, real int" in problemas
    assert "coluna inesperada: extra" in problemas


def test_schema_ignora_caixa_do_tipo():
    assert comparar_schema(ESPERADO, {"evento_id": "STRING", "magnitude": "Double"}) == []


def test_verificar_schema_reprova_com_violacoes():
    resultado = verificar_schema("Q-01a", "silver.sismos", ESPERADO, {"evento_id": "string"})
    assert resultado.violacoes == 1 and resultado.status == "reprovada"
    assert resultado.detalhes == ("coluna ausente: magnitude",)


def test_status_aprovada_reprovada_e_aviso():
    assert regra("erro", 0).status == "aprovada"
    assert regra("erro", 2).status == "reprovada"
    assert regra("aviso", 2).status == "aviso"


def test_taxa_nulos_calcula_fracao_e_trata_tabela_vazia():
    itens = taxa_nulos(200, {"a": 50, "b": 0})
    assert itens[0] == {"coluna": "a", "nulos": 50, "total": 200, "taxa": 0.25}
    assert taxa_nulos(0, {"a": 0})[0]["taxa"] == 0.0


def test_nulos_clima_vira_aviso_e_nao_erro():
    itens = taxa_nulos(100, {"temperatura_c": 3, "umidade_pct": 0})
    resultado = verificar_nulos_clima(itens)
    assert resultado.status == "aviso" and resultado.violacoes == 1
    assert resultado.detalhes == ("temperatura_c: 3 nulos",)
    assert verificar_nulos_clima(taxa_nulos(100, {"a": 0})).status == "aprovada"


def test_contagem_usgs_igual_e_diferente():
    assert verificar_contagem_usgs(224, 224).status == "aprovada"
    reprovada = verificar_contagem_usgs(224, 220)
    assert reprovada.violacoes == 4 and reprovada.status == "reprovada"
    assert "224" in reprovada.detalhes[0] and "220" in reprovada.detalhes[0]


def test_resultado_de_linha_recalcula_o_status():
    linha = {"regra_id": "Q-04", "descricao": "d", "tipo": "unicidade", "nivel": "erro",
             "verificados": 224, "violacoes": 1, "status": "aprovada"}  # status gravado errado de propósito
    assert resultado_de_linha(linha).status == "reprovada"


def test_relatorio_aprovado_quando_so_ha_aviso():
    rel = relatorio([regra("erro", 0, "Q-01"), regra("aviso", 3, "Q-03")])
    assert rel["aprovado"] is True
    assert rel["resumo"] == {"regras": 2, "aprovadas": 1, "reprovadas": 0, "avisos": 1}
    exigir_aprovacao(rel)  # não levanta


def test_relatorio_reprovado_com_regra_de_erro_e_exige_aprovacao_levanta():
    rel = relatorio([regra("erro", 0, "Q-01"), regra("erro", 1, "Q-04")])
    assert rel["aprovado"] is False and rel["resumo"]["reprovadas"] == 1
    with pytest.raises(ErroQualidade, match="Q-04"):
        exigir_aprovacao(rel)


def test_relatorio_ordena_regras_por_id():
    rel = relatorio([regra(regra_id="Q-10"), regra(regra_id="Q-02")])
    assert [r["regra_id"] for r in rel["regras"]] == ["Q-02", "Q-10"]


def test_gravar_relatorio_cria_pasta_preserva_acentos_e_sobrescreve(tmp_path):
    caminho = tmp_path / "reports" / "quality_report.json"
    rel = relatorio([regra()])
    rel["regras"][0]["descricao"] = "descrição com acento"
    gravar_relatorio(rel, caminho)
    assert json.loads(caminho.read_text(encoding="utf-8"))["regras"][0]["descricao"] == "descrição com acento"
    gravar_relatorio(relatorio([regra(), regra(regra_id="Q-98")]), caminho)  # reexecutar sobrescreve
    assert len(json.loads(caminho.read_text(encoding="utf-8"))["regras"]) == 2

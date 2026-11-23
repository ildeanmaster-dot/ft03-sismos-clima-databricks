# Débito técnico
Versão 0.1 · 23/11/2026

| ID | Débito | Impacto | Tipo | Prioridade | Ação | Depende de | Status |
|---|---|---|---|---|---|---|---|
| DT-01 | `run.sh` só informa que o pipeline está em implementação | Sem execução ponta a ponta | Entrega | Alta | Ligar ao job do Databricks | E7, P-04 | Aberto |
| DT-02 | `quality.py` ainda é esqueleto (`config`, `http_client` e `extract` implementados e testados em 23/11/2026) | Qualidade sem código modular | Código | Média | Implementar na E6 | E6 | Aberto |
| DT-03 | Licença do repositório não definida | Reuso do código sem regra | Governança | Baixa | Escolher licença | Ildean | Aberto |
| DT-04 | Limite de taxa numérico da USGS não publicado | Controle de taxa sem número oficial | Fonte | Média | Adotar limite conservador documentado | E1 | Aberto |

Resumo: 4 abertos (2 Alta, 1 Média, 1 Baixa).
| DT-05 | Nome do catálogo (`ft03_sismos_clima`) escrito direto nos SQL de `sql/` | Trocar de catálogo exige editar os arquivos | Código | Baixa | Parametrizar com widget e `IDENTIFIER()` depois que o fluxo estiver completo | E7 | Aberto |
| DT-06 | Esboços `notebooks/02_silver.sql` e `notebooks/03_gold.sql` redundantes com `sql/silver` e `sql/gold` | Dois lugares para a mesma lógica | Estrutura | Baixa | Remover os esboços na limpeza final (exige permissão de exclusão na pasta) | E8 | Aberto |

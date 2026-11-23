# Débito técnico
Versão 0.1 · 23/11/2026

| ID | Débito | Impacto | Tipo | Prioridade | Ação | Depende de | Status |
|---|---|---|---|---|---|---|---|
| DT-01 | `run.sh` só informa que o pipeline está em implementação | Sem execução ponta a ponta | Entrega | Alta | Ligar ao job do Databricks | E7, P-04 | Aberto |
| DT-02 | `quality.py` implementado e testado (13 testes, 31 no total em 23/11/2026), mas ainda não chamado por nenhum notebook | Regras de schema, nulos e USGS sem execução no workspace | Código | Média | Ligar ao notebook `04_qualidade` (E6, parte 4) | E6 | Mitigado |
| DT-03 | Licença do repositório não definida | Reuso do código sem regra | Governança | Baixa | Escolher licença | Ildean | Aberto |
| DT-04 | Limite de taxa numérico da USGS não publicado | Controle de taxa sem número oficial | Fonte | Média | Adotar limite conservador documentado | E1 | Aberto |
| DT-05 | Nome do catálogo (`ft03_sismos_clima`) escrito direto nos SQL de `sql/` | Trocar de catálogo exige editar os arquivos | Código | Baixa | Parametrizar com widget e `IDENTIFIER()` depois que o fluxo estiver completo | E7 | Aberto |
| DT-06 | Esboços `notebooks/02_silver.sql` e `notebooks/03_gold.sql` redundantes com `sql/silver` e `sql/gold` | Dois lugares para a mesma lógica | Estrutura | Baixa | Remover os esboços na limpeza final (exige permissão de exclusão na pasta) | E8 | Aberto |
| DT-07 | A regra Q-06 em `sql/quality/02_regras.sql` usa magnitude mínima 5 fixa | Rodar com outra `magnitude_minima` reprova a Q-06 sem ser erro de dado | Código | Média | Ler `magnitude_minima` do job depois de validar A5 | E7, A5 | Aberto |
| DT-08 | `04_qualidade` lê `gold.qualidade_regras` sem saber quando ela foi gerada | Se `02_regras` não rodar antes, o relatório usa regras defasadas | Código | Média | Garantir a ordem no job (E7) e gravar `executado_em` na tabela | E7 | Aberto |

Resumo: 7 abertos (1 Alta, 3 Média, 3 Baixa) e 1 mitigado (DT-02, Média).
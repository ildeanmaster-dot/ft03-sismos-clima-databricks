# Débito técnico
Versão 0.2 · 24/11/2026

| ID | Débito | Impacto | Tipo | Prioridade | Ação | Depende de | Status |
|---|---|---|---|---|---|---|---|
| DT-01 | `run.sh` só informava que o pipeline estava em implementação | Sem execução ponta a ponta | Entrega | Alta | `run.sh` chama `databricks jobs run-now --json @jobs/run_padrao.json` e espera o fim; execução 357476527649763 com `SUCCESS` e código de saída 0; falta validar o código de saída com o job em FAILED | E7, P-04 | Resolvido (24/11/2026, OB-40) |
| DT-02 | `quality.py` era esqueleto | Qualidade sem código modular | Código | Média | Implementar e ligar ao notebook | E6 | Resolvido (23/11/2026, OB-33) |
| DT-03 | Licença do repositório não definida | Reuso do código sem regra | Governança | Baixa | Escolher licença | Ildean | Aberto |
| DT-04 | Limite de taxa numérico da USGS não publicado | Controle de taxa sem número oficial | Fonte | Média | Adotar limite conservador documentado | E1 | Aberto |
| DT-05 | Nome do catálogo (`ft03_sismos_clima`) escrito direto nos SQL de `sql/` | Trocar de catálogo exige editar os arquivos | Código | Baixa | Parametrizar com widget e `IDENTIFIER()` depois que o fluxo estiver completo | E7 | Aberto |
| DT-06 | Esboços `notebooks/02_silver.sql` e `notebooks/03_gold.sql` redundantes com `sql/silver` e `sql/gold` | Dois lugares para a mesma lógica | Estrutura | Baixa | Esboços removidos com `git rm` (24/11/2026); o Pull no Git folder os tira do workspace | E8 | Resolvido (24/11/2026) |
| DT-07 | A regra Q-06 em `sql/quality/02_regras.sql` usa magnitude mínima 5 fixa | Rodar com outra `magnitude_minima` reprova a Q-06 sem ser erro de dado | Código | Média | Ler `magnitude_minima` do job depois de validar A5 | E7, A5 | Aberto |
| DT-08 | `04_qualidade` lê `gold.qualidade_regras` sem saber quando ela foi gerada | Se `02_regras` não rodar antes, o relatório usa regras defasadas | Código | Média | Garantir a ordem no job (E7) e gravar `executado_em` na tabela | E7 | Aberto |
| DT-09 | A extração não limpava o volume `raw`: arquivos de períodos anteriores continuavam e a bronze lê a pasta inteira | Rodar outro período mistura eventos antigos na bronze; a Q-10 reprova (OB-38) e a silver só se salva pela deduplicação | Código | Média | `limpar_raw` em `extract.py` apaga os .json de `usgs/` e `open_meteo/` depois de a USGS responder (D-06); 34 testes passam; `Path.unlink` validado no volume (226 arquivos removidos na execução 842064343772824) | E7 | Resolvido (24/11/2026, OB-39) |
| DT-10 | Pasta `raw/_teste` no volume `bronze.raw` com os arquivos do teste de extração de 23/11/2026 (OB-18) | Arquivos fora do fluxo no volume; a bronze não lê essa pasta | Ambiente | Baixa | Apagar a pasta no workspace | Ildean | Aberto |
| DT-11 | 4 notebooks rascunho na Home do workspace, fora do Git folder (`00_validacao_apis`, `01_ambiente`, `02_teste_import`, `03_explorar_bronze`) | Confusão com os notebooks versionados | Ambiente | Baixa | Apagar ou mover para uma pasta de arquivo | Ildean | Aberto |

Resumo: 7 abertos (3 Média, 4 Baixa) e 4 resolvidos (DT-01, DT-02, DT-06, DT-09).
# Portal do projeto

`index.html` é o portal do projeto em **um único arquivo** que abre offline (Chrome ou Edge). É **gerado** a partir dos documentos: não editar à mão.

## O que tem
| Seção | De onde vem |
|---|---|
| Painel e Progresso | `docs/00-gestao/estado-do-projeto.md`, regras, requisitos, débitos, pendências e CHANGELOG |
| Apresentação técnica | `docs/04-apresentacao/apresentacao-tecnica.md` (diagramas Mermaid) |
| Termo, Regras, Requisitos, Decisões | documentos de `docs/00-gestao` e `docs/01-negocio` |
| Arquitetura e processo | blocos `mermaid` de `docs/02-arquitetura/arquitetura-da-solucao.md` e `diagramas.md`, um por aba |
| Débito técnico, Observações, Riscos, Histórico | documentos correspondentes |
| Todos os documentos | todos os `.md` de `docs/` e os README da raiz, com busca |

## Como regerar
```
python portal/gerar_portal.py
```
Saída esperada: `portal/index.html: N KB · N documentos · 11 regras · 15 requisitos · 9 débitos · 0 fluxos · N diagramas · 0 fluxogramas`. Rodar depois de mudar qualquer documento.

## Arquivos
| Arquivo | Papel |
|---|---|
| `gerar_portal.py` | Gerador (só biblioteca padrão do Python) |
| `modelo/portal.html`, `portal.css`, `portal.js` | Modelo da página, igual ao dos outros portais da Yottaflow |
| `dados/portal.json` | Nome, cores, menu e caminhos dos documentos; sem logotipo (não há marca de cliente) |
| `dados/licenciamento.json` | Vazio: o projeto não usa licença paga (a seção está fora do menu) |
| `vendor/` | `mermaid.min.js` 11.12.0 e `marked.min.js` 15.0.12 (licença MIT) |

Regra: nada é inventado no portal; o que não está nos documentos ou no código não aparece.

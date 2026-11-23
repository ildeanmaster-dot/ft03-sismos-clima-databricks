# Riscos
Versão 0.1 · 23/11/2026

| # | Risco | Efeito | Resposta |
|---|---|---|---|
| R-01 | USGS e Open-Meteo são ambas ciências da Terra; avaliador pode questionar "domínios distintos" | Requisito contestado | Provedores e áreas diferentes (sismologia × meteorologia); confirmar com a turma (P-05) |
| R-02 | Cota diária do Free Edition derruba o compute | Execução adiada | Período pequeno e job enxuto |
| R-03 | Domínio liberado hoje pode ser bloqueado depois | Extração falha | Guardar o bruto no volume bronze; reprocessar sem chamar a API |
| R-04 | Evento revisado pela USGS (campo `updated`) muda magnitude ou posição | Duplicata ou valor antigo | Deduplicar por `id` mantendo o maior `updated` |

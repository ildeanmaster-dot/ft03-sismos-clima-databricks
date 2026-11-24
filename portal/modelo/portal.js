(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("dados").textContent);
  var C = D.cores;
  var main = document.getElementById("conteudo");

  // ------------------------------------------------------------ utilidades
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function inline(s) { return marked.parseInline(String(s == null ? "" : s)); }
  function el(html) { main.innerHTML = html; main.focus({ preventScroll: true }); window.scrollTo(0, 0); }
  function doc(caminho) { for (var i = 0; i < D.docs.length; i++) if (D.docs[i].caminho === caminho) return D.docs[i]; return null; }
  function contar(lista, campo) { var o = {}; lista.forEach(function (x) { var k = x[campo] || "Outro"; o[k] = (o[k] || 0) + 1; }); return o; }
  function plain(s) { return String(s || "").replace(/\*\*/g, "").replace(/`/g, ""); }
  var nfR = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  function brl(v) { return "R$ " + nfR.format(v); }
  function usd(v) { return "US$ " + nfR.format(v); }

  var CLASSE = {
    "Implementado": "s-ok", "Testado": "s-ok", "Resolvido": "s-ok", "Provisório": "s-prov", "Parcial": "s-parcial",
    "Pendente": "s-pend", "Aguarda": "s-pend", "Aberto": "s-nao", "Não implementado": "s-nao", "Esqueleto": "s-esq",
    "Mitigado": "s-esq", "Aceito": "s-esq", "Processo": "s-info", "Informativo": "s-info", "Outro": "s-info",
    "Alta": "s-alta", "Média": "s-media", "Baixa": "s-baixa"
  };
  var COR_STATUS = {
    "Implementado": "#54AF3B", "Provisório": "#FEBA02", "Parcial": "#C4930F", "Esqueleto": "#5CACEB",
    "Pendente": "#D2D6E0", "Não implementado": "#D43416", "Processo": "#E6E2F5", "Informativo": "#E6E2F5", "Outro": "#ACB0BC"
  };
  function chip(base, texto) { return '<span class="chip ' + (CLASSE[base] || "s-info") + '">' + esc(texto || base) + "</span>"; }
  function barra(cont, ordem) {
    var total = 0; ordem.forEach(function (k) { total += cont[k] || 0; });
    var b = '<div class="barra" role="img" aria-label="' + esc(ordem.map(function (k) { return k + ": " + (cont[k] || 0); }).join(", ")) + '">';
    ordem.forEach(function (k) { if (cont[k]) b += '<span style="width:' + (100 * cont[k] / total) + "%;background:" + (COR_STATUS[k] || "#ACB0BC") + '"></span>'; });
    b += '</div><div class="legenda">';
    ordem.forEach(function (k) { if (cont[k]) b += '<span><i style="background:' + (COR_STATUS[k] || "#ACB0BC") + '"></i>' + esc(k) + " " + cont[k] + "</span>"; });
    return b + "</div>";
  }

  // ------------------------------------------------------------ Markdown e Mermaid
  mermaid.initialize({
    startOnLoad: false, securityLevel: "strict", theme: "base",
    flowchart: { htmlLabels: true, curve: "basis", useMaxWidth: false },
    themeVariables: {
      fontFamily: D.fonte, fontSize: "13px", primaryColor: "#FFFFFF", primaryBorderColor: C.borda_campo || C["borda-campo"] || "#ACB0BC",
      primaryTextColor: C.texto, lineColor: "#5C5C5C", clusterBkg: "#FAFAFB", clusterBorder: C.borda, tertiaryColor: C.tinta2
    }
  });
  var seq = 0;
  async function desenhar(raiz) {
    var nos = raiz.querySelectorAll("pre > code.language-mermaid, div.mermaid-fonte");
    for (var i = 0; i < nos.length; i++) {
      var n = nos[i], fonte = n.textContent, alvo = n.tagName === "CODE" ? n.parentNode : n;
      var caixa = document.createElement("div"); caixa.className = "diagrama";
      try {
        var r = await mermaid.render("mmd" + (++seq), fonte);
        caixa.innerHTML = r.svg;
      } catch (e) {
        caixa.innerHTML = '<p class="nota">Não foi possível desenhar este diagrama: ' + esc(e.message || e) + "</p><pre>" + esc(fonte) + "</pre>";
      }
      alvo.parentNode.replaceChild(caixa, alvo);
    }
  }
  function linksDocs(raiz, base) {
    raiz.querySelectorAll("a[href]").forEach(function (a) {
      var h = a.getAttribute("href");
      if (/^(https?:|mailto:|#)/.test(h) || !/\.md(#.*)?$/.test(h)) return;
      var partes = (base.split("/").slice(0, -1).join("/") + "/" + h.replace(/#.*$/, "")).split("/"), pilha = [];
      partes.forEach(function (p) { if (p === "..") pilha.pop(); else if (p && p !== ".") pilha.push(p); });
      var alvo = pilha.join("/");
      if (doc(alvo)) a.setAttribute("href", "#doc/" + encodeURIComponent(alvo));
    });
    raiz.querySelectorAll("code").forEach(function (c) {
      var t = c.textContent.trim();
      if (c.parentNode.tagName === "A" || c.parentNode.tagName === "PRE") return;
      var cand = D.docs.filter(function (d) { return d.caminho === t || d.caminho.endsWith("/" + t); });
      if (cand.length === 1) { var a = document.createElement("a"); a.href = "#doc/" + encodeURIComponent(cand[0].caminho); c.parentNode.replaceChild(a, c); a.appendChild(c); }
    });
  }
  async function renderMd(md, caminho, alvo) {
    alvo.innerHTML = marked.parse(md, { gfm: true });
    alvo.querySelectorAll("table").forEach(function (t) { var w = document.createElement("div"); w.className = "tabela"; t.parentNode.insertBefore(w, t); w.appendChild(t); });
    linksDocs(alvo, caminho || "");
    await desenhar(alvo);
  }
  async function paginaDoc(caminho, titulo, sub) {
    var d = doc(caminho);
    if (!d) { el('<h1>Documento não encontrado</h1><p class="sub">' + esc(caminho) + "</p>"); return; }
    el((titulo ? "<h1>" + titulo + '</h1><p class="sub">' + esc(sub || "") + " · fonte: <code>" + esc(caminho) + "</code></p>" : "") + '<article class="doc" id="docCorpo"></article>');
    await renderMd(d.md, caminho, document.getElementById("docCorpo"));
  }

  // ------------------------------------------------------------ páginas
  function contagemStatus(lista) { return contar(lista, "status_base"); }
  var ORDEM_RN = ["Implementado", "Provisório", "Parcial", "Esqueleto", "Pendente", "Não implementado", "Processo", "Informativo", "Outro"];

  function painel() {
    var rn = contagemStatus(D.regras), rf = contagemStatus(D.requisitos.filter(function (r) { return r.tipo === "Funcional"; }));
    var abertos = D.debitos.filter(function (d) { return d.status_base === "Aberto"; });
    var porPr = contar(abertos, "prioridade");
    var lig = D.fluxos.filter(function (f) { return /^ligado/i.test(f.estado); }).length;
    var h = "<h1><b>" + esc(D.projeto.titulo) + "</b> · " + esc(D.projeto.cliente) + '</h1><p class="sub">' + esc(D.projeto.subtitulo) + ". Gerado em " + esc(D.gerado_em) + " a partir dos documentos e do código do repositório.</p>";
    h += '<div class="grade g4">';
    h += '<div class="kpi"><div class="rotulo">Regras de negócio implementadas</div><div class="valor">' + (rn["Implementado"] || 0) + " / " + D.regras.length + "</div>" + barra(rn, ORDEM_RN) + "</div>";
    h += '<div class="kpi"><div class="rotulo">Requisitos funcionais implementados</div><div class="valor">' + (rf["Implementado"] || 0) + " / " + D.requisitos.filter(function (r) { return r.tipo === "Funcional"; }).length + "</div>" + barra(rf, ORDEM_RN) + "</div>";
    if (D.fluxos.length) h += '<div class="kpi"><div class="rotulo">Fluxos ligados</div><div class="valor">' + lig + " / " + D.fluxos.length + '</div><div class="det">' + D.fluxos.filter(function (f) { return !/^ligado/i.test(f.estado); }).map(function (f) { return esc(f.codigo + " " + f.estado.toLowerCase()); }).join(" · ") + "</div></div>";
    else h += '<div class="kpi"><div class="rotulo">Pendências com o cliente</div><div class="valor">' + D.pendencias.length + '</div><div class="det">' + esc((D.painel && D.painel.kpi_pendencias) || "abertas em decisões e pendências") + "</div></div>";
    h += '<div class="kpi"><div class="rotulo">Débitos técnicos abertos</div><div class="valor">' + abertos.length + '</div><div class="det">' + ["Alta", "Média", "Baixa"].map(function (p) { return chip(p, p + " " + (porPr[p] || 0)); }).join(" ") + "</div></div>";
    h += "</div>";
    var mk = D.painel && D.painel.mockup;
    if (mk && mk.url) h += '<div class="cartao atalho-mockup"><div><b>' + esc(mk.t || "Mockup") + "</b>" + (mk.texto ? '<div class="det">' + esc(mk.texto) + "</div>" : "") + '</div><a class="botao" href="' + esc(mk.url) + '" target="_blank" rel="noopener">' + esc(mk.botao || "Abrir mockup") + " ↗</a></div>";
    h += "<h2>Etapas</h2>" + tabelaSimples(["Etapa", "Situação", "O que falta"], D.etapas);
    h += '<div class="grade g2"><div><h2>Pendências com o cliente (' + D.pendencias.length + ')</h2>' + tabelaSimples(["#", "Pendência", "Bloqueia", "Com quem"], D.pendencias.map(function (p) { return [p.id, p.texto, p.bloqueia, p.com]; })) + "</div>";
    h += "<div><h2>Próximos passos</h2>" + tabelaSimples(["#", "Ação", "Quem"], D.proximos) + "<h2>Últimas mudanças</h2>";
    D.historico.slice(0, 3).forEach(function (x) { h += '<div class="cartao"><b>' + inline(x.titulo) + "</b><ul>" + x.itens.slice(0, 4).map(function (i) { return "<li>" + inline(i) + "</li>"; }).join("") + "</ul></div>"; });
    h += "</div></div>";
    el(h);
  }
  function tabelaSimples(cab, linhas) {
    var h = '<div class="tabela"><table><thead><tr>' + cab.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>";
    linhas.forEach(function (l) { h += "<tr>" + l.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>"; });
    return h + "</tbody></table></div>";
  }

  function progresso() {
    var h = '<h1><b>Progresso</b> do projeto</h1><p class="sub">Fonte: <a href="#doc/' + encodeURIComponent(D.fontes.estado) + '">' + esc(D.fontes.estado) + "</a> e CHANGELOG.</p>";
    h += "<h2>Etapas</h2>" + tabelaSimples(["Etapa", "Situação", "O que falta"], D.etapas);
    h += "<h2>Componentes</h2>" + tabelaSimples(["Componente", "Situação", "Evidência"], D.componentes);
    h += "<h2>Histórico</h2>";
    D.historico.forEach(function (x) { h += '<div class="cartao"><b>' + inline(x.titulo) + "</b><ul>" + x.itens.map(function (i) { return "<li>" + inline(i) + "</li>"; }).join("") + "</ul></div>"; });
    el(h);
  }

  function tabelaFiltravel(cfg) {
    var lista = cfg.lista, id = cfg.id;
    var h = "<h1>" + cfg.titulo + '</h1><p class="sub">' + cfg.sub + '</p><div class="cartao">' + barra(contar(lista, cfg.campoStatus), cfg.ordem) + "</div>";
    h += '<div class="filtros">';
    cfg.filtros.forEach(function (f) {
      var vals = Array.from(new Set(lista.map(function (x) { return x[f.campo]; }))).filter(Boolean);
      h += '<label>' + esc(f.rotulo) + ' <select data-campo="' + f.campo + '"><option value="">Todos</option>' + vals.map(function (v) { return "<option>" + esc(v) + "</option>"; }).join("") + "</select></label>";
    });
    h += '<input type="search" placeholder="Filtrar texto" id="' + id + 'Txt" aria-label="Filtrar texto"><span class="contagem" id="' + id + 'Cont"></span></div>';
    h += '<div class="tabela"><table><thead><tr>' + cfg.colunas.map(function (c) { return "<th>" + esc(c.rotulo) + "</th>"; }).join("") + '</tr></thead><tbody id="' + id + 'Corpo"></tbody></table></div>';
    el(h);
    function aplicar() {
      var sel = {}; main.querySelectorAll(".filtros select").forEach(function (s) { sel[s.dataset.campo] = s.value; });
      var txt = document.getElementById(id + "Txt").value.toLowerCase();
      var vis = lista.filter(function (x) {
        for (var k in sel) if (sel[k] && x[k] !== sel[k]) return false;
        return !txt || JSON.stringify(x).toLowerCase().indexOf(txt) >= 0;
      });
      document.getElementById(id + "Corpo").innerHTML = vis.map(function (x) {
        return "<tr>" + cfg.colunas.map(function (c) { return "<td>" + (c.render ? c.render(x) : inline(x[c.campo])) + "</td>"; }).join("") + "</tr>";
      }).join("");
      document.getElementById(id + "Cont").textContent = vis.length + " de " + lista.length;
    }
    main.querySelectorAll(".filtros select, .filtros input").forEach(function (e) { e.addEventListener("input", aplicar); });
    aplicar();
  }
  function regras() {
    tabelaFiltravel({
      id: "rn", titulo: "<b>Regras</b> de negócio", lista: D.regras, campoStatus: "status_base", ordem: ORDEM_RN,
      sub: D.regras.length + ' regras com o status atual. Fonte: <a href="#doc/' + encodeURIComponent(D.fontes.regras) + '">' + esc(D.fontes.regras) + "</a>.",
      filtros: [{ campo: "area", rotulo: "Área" }, { campo: "status_base", rotulo: "Status" }],
      colunas: [{ rotulo: "ID", campo: "id", render: function (x) { return "<b>" + esc(x.id) + "</b>"; } }, { rotulo: "Regra", campo: "regra" }, { rotulo: "Origem", campo: "origem" },
        { rotulo: "Status", campo: "status", render: function (x) { return chip(x.status_base, x.status_base) + "<br><span class='nota'>" + inline(x.status) + "</span>"; } }, { rotulo: "Onde está", campo: "onde" }]
    });
  }
  function requisitos() {
    tabelaFiltravel({
      id: "rq", titulo: "<b>Requisitos</b>", lista: D.requisitos, campoStatus: "status_base", ordem: ORDEM_RN,
      sub: 'Funcionais e não funcionais. Fonte: <a href="#doc/' + encodeURIComponent(D.fontes.requisitos) + '">' + esc(D.fontes.requisitos) + "</a>.",
      filtros: [{ campo: "tipo", rotulo: "Tipo" }, { campo: "status_base", rotulo: "Status" }, { campo: "prioridade", rotulo: "Prioridade" }],
      colunas: [{ rotulo: "ID", campo: "id", render: function (x) { return "<b>" + esc(x.id) + "</b>"; } }, { rotulo: "Requisito", campo: "texto" }, { rotulo: "Prior.", campo: "prioridade" },
        { rotulo: "Status", campo: "status", render: function (x) { return chip(x.status_base, x.status_base) + "<br><span class='nota'>" + inline(x.status) + "</span>"; } }]
    });
  }
  function debito() {
    tabelaFiltravel({
      id: "dt", titulo: "<b>Débito</b> técnico", lista: D.debitos, campoStatus: "status_base", ordem: ["Aberto", "Mitigado", "Aceito", "Resolvido"],
      sub: 'Fonte: <a href="#doc/' + encodeURIComponent(D.fontes.debito) + '">' + esc(D.fontes.debito) + "</a>.",
      filtros: [{ campo: "prioridade", rotulo: "Prioridade" }, { campo: "status_base", rotulo: "Status" }, { campo: "tipo", rotulo: "Tipo" }],
      colunas: [{ rotulo: "ID", campo: "id", render: function (x) { return "<b>" + esc(x.id) + "</b>"; } }, { rotulo: "Débito", campo: "texto" }, { rotulo: "Impacto", campo: "impacto" },
        { rotulo: "Prioridade", campo: "prioridade", render: function (x) { return chip(x.prioridade); } }, { rotulo: "Ação", campo: "acao" }, { rotulo: "Depende de", campo: "depende" },
        { rotulo: "Status", campo: "status", render: function (x) { return chip(x.status_base, x.status); } }]
    });
  }

  async function arquitetura(aba) {
    var abas = D.diagramas.map(function (d, i) { return { id: "d" + i, titulo: d.titulo }; });
    D.fluxogramas.forEach(function (f, i) { abas.push({ id: "f" + i, titulo: f.titulo }); });
    aba = aba || "d0";
    var h = '<h1><b>Arquitetura</b> e processo</h1><p class="sub">Várias visões do mesmo ecossistema. Diagramas tirados de <code>' + esc(D.fontes.arquitetura) + "</code>, <code>" + esc(D.fontes.diagramas) + "</code> e dos fluxogramas do processo.</p>";
    h += '<div class="abas" role="tablist">' + abas.map(function (a) { return '<button role="tab" aria-selected="' + (a.id === aba) + '" data-aba="' + a.id + '">' + esc(a.titulo) + "</button>"; }).join("") + "</div>";
    h += '<div id="painelAba"></div>';
    el(h);
    main.querySelectorAll(".abas button").forEach(function (b) { b.addEventListener("click", function () { location.hash = "#arquitetura/" + b.dataset.aba; }); });
    var alvo = document.getElementById("painelAba");
    if (aba[0] === "d") {
      var d = D.diagramas[+aba.slice(1)];
      alvo.innerHTML = (d.texto ? '<div class="cartao" id="txtDiag"></div>' : "") + '<div class="mermaid-fonte"></div><p class="nota">Fonte: ' + esc(d.fonte) + "</p>";
      if (d.texto) document.getElementById("txtDiag").innerHTML = marked.parse(d.texto);
      alvo.querySelector(".mermaid-fonte").textContent = d.mermaid;
      await desenhar(alvo);
    } else {
      var f = D.fluxogramas[+aba.slice(1)];
      alvo.innerHTML = '<div class="diagrama"><img alt="' + esc(f.titulo) + '" src="' + f.src + '"></div><p class="nota">Fonte: ' + esc(f.arquivo) + "</p>";
    }
  }

  function fluxos() {
    var h = '<h1><b>Fluxos</b> Power Automate</h1><p class="sub">' + D.fluxos.length + ' fluxos da solução. Cada diagrama é gerado das definições implantadas (<code>' + esc(D.fontes.pasta_fluxos) + '/definitions</code>), sem desenho à mão.</p>';
    h += '<div class="lista-fluxos">';
    D.fluxos.forEach(function (f) {
      h += '<a class="fluxo-card" href="#fluxo/' + f.codigo + '"><h3>' + esc(f.nome) + "</h3>" + chip(/^ligado/i.test(f.estado) ? "Implementado" : "Pendente", f.estado || "sem estado") +
        " " + (f.premium ? '<span class="chip s-info">premium</span>' : '<span class="chip s-pend">só padrão</span>') +
        "<p>" + esc(f.gatilho) + "</p><p>" + f.n_acoes + " ações · " + esc(f.conexoes.join(", ")) + (f.pendentes.length ? " · " + f.pendentes.length + " pendência(s)" : "") + "</p></a>";
    });
    h += "</div>";
    el(h);
  }
  async function fluxo(cod) {
    var f = D.fluxos.filter(function (x) { return x.codigo === cod; })[0];
    if (!f) { fluxos(); return; }
    var h = '<p><a href="#fluxos">← Todos os fluxos</a></p><h1>' + esc(f.nome) + '</h1><p class="sub">' + esc(f.descricao) + "</p>";
    h += '<div class="grade g4"><div class="kpi"><div class="rotulo">' + esc((D.painel && D.painel.rotulo_estado_fluxo) || "Estado no DEV") + '</div><div class="valor" style="font-size:18px">' + esc(f.estado || "–") + '</div><div class="det">' + inline(f.motivo) + '</div></div>' +
      '<div class="kpi"><div class="rotulo">Gatilho</div><div class="det" style="font-size:13px;color:inherit">' + esc(f.gatilho) + "</div></div>" +
      '<div class="kpi"><div class="rotulo">Conexões</div><div class="det" style="font-size:13px;color:inherit">' + esc(f.conexoes.join(", ")) + (f.premium ? " · premium" : " · só padrão") + "</div></div>" +
      '<div class="kpi"><div class="rotulo">Ações</div><div class="valor">' + f.n_acoes + "</div></div></div>";
    if (f.teste) h += '<div class="cartao"><b>Teste feito:</b> ' + inline(f.teste) + "</div>";
    h += '<h2>Diagrama</h2><div class="legenda-fluxo"><span><i style="border-color:#242424;background:#242424"></i>Gatilho</span><span><i style="border-color:#5CACEB"></i>SharePoint</span><span><i style="border-color:#57479C;background:#F4F2FB"></i>Premium (HTTP, Dataverse)</span><span><i style="border-color:#8F7ED7"></i>Teams</span><span><i style="border-color:#57479C;background:#E6E2F5"></i>Fluxo filho</span><span><i style="border-color:#D43416"></i>Responder ou encerrar</span><span><i style="border-color:#687FA4"></i>Outros conectores padrão (Outlook, Excel, Aprovações)</span><span><i style="border-color:#ACB0BC"></i>Controle e dados</span><span>linha tracejada = executa após falha, ignorado ou tempo esgotado</span></div>';
    h += '<div class="mermaid-fonte" id="mmdFluxo"></div>';
    if (f.pendentes.length) h += "<h2>Pendências marcadas no fluxo</h2>" + tabelaSimples(["Ação", "Descrição"], f.pendentes.map(function (a) { return [a.nome, a.descricao]; }));
    h += "<h2>Ações</h2>" + tabelaSimples(["Ação", "Tipo", "Dentro de", "Detalhe", "Descrição"], f.acoes.map(function (a) { return [a.nome, a.tipo, a.dentro, "`" + a.detalhe.replace(/`/g, "") + "`", a.descricao]; }).map(function (r) { if (r[3] === "``") r[3] = ""; return r; }));
    if (f.parametros.length) h += "<h2>Variáveis de ambiente usadas</h2><ul>" + f.parametros.map(function (p) { return "<li>" + esc(p) + "</li>"; }).join("") + "</ul>";
    el(h);
    document.getElementById("mmdFluxo").textContent = f.mermaid;
    await desenhar(main);
  }

  function licencas() {
    var L = D.licenciamento, porId = {};
    L.licencas.forEach(function (l) { porId[l.id] = l; });
    var h = '<h1><b>Licenciamento</b></h1><p class="sub">Cenários com preços de lista oficiais consultados em ' + esc(L.consultado_em) + ". " + esc(L.observacao) + "</p>";
    h += '<div class="cartao filtros"><label for="nUsu"><b>Usuários do app</b></label><input id="nUsu" type="number" min="1" max="500" value="' + L.usuarios_padrao + '" style="width:90px"><span class="nota">Muda os totais dos cenários que cobram por usuário.</span></div>';
    h += '<div class="cenarios" id="cenarios"></div>';
    h += "<h2>Preços de lista</h2>" + tabelaSimples(["Licença", "US$", "R$", "Unidade", "Inclui"], L.licencas.map(function (l) { return [l.nome, usd(l.usd), brl(l.brl), l.unidade, l.inclui]; }));
    h += "<h2>Regras que decidem o cenário (FAQ do Learn)</h2>" + tabelaSimples(["#", "Regra"], L.regras.map(function (r) { return [r.id, r.texto]; }));
    h += "<h2>Fora destes valores</h2><ul>" + L.fora_dos_valores.map(function (t) { return "<li>" + inline(t) + "</li>"; }).join("") + "</ul>";
    h += "<h2>Fontes</h2><ul>" + L.fontes.map(function (f) { return '<li><a href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.titulo) + "</a></li>"; }).join("") + "</ul>";
    h += '<p class="nota">Detalhe e enquadramento de cada fluxo: <a href="#doc/' + encodeURIComponent(D.fontes.licenciamento_doc) + '">' + esc(D.fontes.licenciamento_doc) + "</a>.</p>";
    el(h);
    function calc() {
      var u = Math.max(1, parseInt(document.getElementById("nUsu").value, 10) || 1);
      document.getElementById("cenarios").innerHTML = L.cenarios.map(function (c) {
        var tu = 0, tb = 0, linhas = c.itens.map(function (it) {
          var q = it.qtd === "u" ? u : parseInt(it.qtd, 10), l = porId[it.licenca];
          tu += q * l.usd; tb += q * l.brl;
          return "<li>" + q + " × " + esc(l.nome) + " <span class='nota'>(" + esc(it.para) + ")</span></li>";
        }).join("");
        var conf = c.conformidade === "sim" ? chip("Implementado", "Conforme") : chip("Parcial", "Conforme em parte");
        return '<div class="cenario' + (c.recomendado ? " rec" : "") + '">' + (c.recomendado ? '<span class="selo">Recomendado</span>' : "") +
          "<h3>" + esc(c.nome) + '</h3><div class="nota">' + esc(c.subtitulo) + "</div><ul>" + linhas + "</ul>" +
          '<div class="preco">' + brl(tb) + ' <small>/mês</small></div><div>' + usd(tu) + ' <small class="nota">/mês</small></div>' +
          '<div class="nota">Anual: ' + brl(tb * 12) + " · " + usd(tu * 12) + "</div>" +
          '<div class="conf">' + conf + "<p>" + esc(c.conformidade_texto) + "</p><p><b>Arquitetura:</b> " + esc(c.arquitetura) + "</p><p><b>Escala:</b> " + esc(c.escala) + "</p></div></div>";
      }).join("");
    }
    document.getElementById("nUsu").addEventListener("input", calc);
    calc();
  }

  function documentos() {
    var grupos = {};
    D.docs.forEach(function (d) { (grupos[d.grupo] = grupos[d.grupo] || []).push(d); });
    var h = '<h1><b>Documentos</b></h1><p class="sub">' + D.docs.length + " documentos do repositório, lidos na geração do portal.</p><div class=\"cartao arvore\">";
    Object.keys(grupos).forEach(function (g) {
      h += "<h3>" + esc(g) + "</h3><ul>" + grupos[g].map(function (d) { return '<li><a href="#doc/' + encodeURIComponent(d.caminho) + '">' + esc(plain(d.titulo)) + "</a>" + (d.versao ? ' <span class="nota">' + esc(d.versao) + "</span>" : "") + "</li>"; }).join("") + "</ul>";
    });
    el(h + "</div>");
  }
  function busca(q) {
    q = q.trim().toLowerCase();
    if (q.length < 2) { documentos(); return; }
    var res = [];
    D.docs.forEach(function (d) {
      var i = d.md.toLowerCase().indexOf(q);
      if (i >= 0) {
        var n = d.md.toLowerCase().split(q).length - 1;
        var trecho = d.md.slice(Math.max(0, i - 80), i + q.length + 120).replace(/\n/g, " ");
        res.push({ d: d, n: n, t: trecho });
      }
    });
    res.sort(function (a, b) { return b.n - a.n; });
    var h = "<h1>Busca: " + esc(q) + '</h1><p class="sub">' + res.length + " documento(s).</p>";
    res.forEach(function (r) {
      var t = esc(r.t).replace(new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig"), function (m) { return '<mark class="marca-busca">' + m + "</mark>"; });
      h += '<div class="cartao resultado-busca"><a href="#doc/' + encodeURIComponent(r.d.caminho) + '"><b>' + esc(plain(r.d.titulo)) + "</b></a> <span class='nota'>" + esc(r.d.caminho) + " · " + r.n + " ocorrência(s)</span><p>…" + t + "…</p></div>";
    });
    el(h);
  }

  // ------------------------------------------------------------ menu e rotas
  // Menu: vem de portal/dados/portal.json ("menu"); itens {g} = grupo, {id,t} = página nativa, {id,t,doc,sub} = documento Markdown,
  // {t,url} = link para arquivo ou site, aberto em nova aba (caminho relativo ao portal/index.html).
  var MENU = D.menu || [
    { g: "Acompanhamento" }, { id: "painel", t: "Painel" }, { id: "progresso", t: "Progresso" }, { id: "termo", t: "Termo de abertura" },
    { g: "Negócio" }, { id: "regras", t: "Regras de negócio" }, { id: "requisitos", t: "Requisitos" }, { id: "decisoes", t: "Decisões e pendências" },
    { g: "Solução" }, { id: "arquitetura", t: "Arquitetura e processo" }, { id: "fluxos", t: "Fluxos Power Automate" }, { id: "app", t: "App Power Apps" }, { id: "dados", t: "Dados (SharePoint)" },
    { g: "Gestão" }, { id: "licencas", t: "Licenciamento" }, { id: "debito", t: "Débito técnico" }, { id: "observacoes", t: "Observações e lições" },
    { g: "Referência" }, { id: "docs", t: "Todos os documentos" }, { id: "historico", t: "Histórico de mudanças" }
  ];
  var ROTAS = {
    painel: painel, progresso: progresso, regras: regras, requisitos: requisitos, debito: debito, fluxos: fluxos, licencas: licencas, docs: documentos,
    termo: function () { return paginaDoc(D.fontes.termo, "<b>Termo</b> de abertura", "Objetivo, escopo, entregas, premissas, riscos e marcos"); },
    decisoes: function () { return paginaDoc(D.fontes.decisoes, "<b>Decisões</b> e pendências", "Decisões do cliente e pendências abertas"); },
    app: function () { return paginaDoc(D.fontes.app, "<b>App</b> Power Apps", "Telas, padrões, delegação, perfis e validação"); },
    dados: function () { return paginaDoc(D.fontes.dicionario, "<b>Dados</b> no SharePoint", "Dicionário gerado do script de provisionamento"); },
    observacoes: function () { return paginaDoc(D.fontes.observacoes, "<b>Observações</b> e lições", "Achados da construção e da validação"); },
    historico: function () { return paginaDoc(D.fontes.changelog, "<b>Histórico</b> de mudanças", "CHANGELOG do projeto"); }
  };
  MENU.forEach(function (m) {
    if (m.id && m.doc) {
      ROTAS[m.id] = function () { var t = m.t.split(" "); return paginaDoc(m.doc, "<b>" + esc(t[0]) + "</b> " + esc(t.slice(1).join(" ")), m.sub || ""); };
    }
  });
  function montarMenu() {
    document.getElementById("logo").src = D.logo;
    document.getElementById("logo").alt = D.projeto.cliente;
    document.getElementById("menuProjeto").innerHTML = "<b>" + esc(D.projeto.titulo) + "</b>" + esc(D.projeto.subtitulo);
    document.getElementById("menuRodape").innerHTML = esc(D.projeto.fornecedor) + "<br>Gerado em " + esc(D.gerado_em);
    document.getElementById("menuLista").innerHTML = MENU.map(function (m) {
      if (m.g) return '<li class="grupo">' + esc(m.g) + "</li>";
      if (m.url) return '<li><a href="' + esc(m.url) + '" target="_blank" rel="noopener">' + esc(m.t) + " ↗</a></li>";
      return '<li><a href="#' + m.id + '" data-id="' + m.id + '">' + esc(m.t) + "</a></li>";
    }).join("");
  }
  async function rota() {
    var h = decodeURIComponent(location.hash.replace(/^#/, "")) || "painel";
    var partes = h.split("/"), base = partes[0];
    document.querySelectorAll("#menuLista a").forEach(function (a) {
      var ativo = a.dataset.id === base || (base === "fluxo" && a.dataset.id === "fluxos") || (base === "doc" && a.dataset.id === "docs");
      if (ativo) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    var item = MENU.filter(function (m) { return m.id === base; })[0];
    document.getElementById("topoTitulo").innerHTML = "<b>" + esc(D.projeto.cliente) + "</b> · " + esc(item ? item.t : base === "fluxo" ? "Fluxo " + (partes[1] || "") : base === "doc" ? "Documento" : "");
    document.getElementById("menu").classList.remove("aberto");
    try {
      if (base === "fluxo") await fluxo(partes[1]);
      else if (base === "doc") await paginaDoc(partes.slice(1).join("/"), "", "");
      else if (base === "arquitetura") await arquitetura(partes[1]);
      else if (base === "busca") busca(partes.slice(1).join("/"));
      else await (ROTAS[base] || painel)();
    } catch (e) {
      main.innerHTML = '<div class="cartao"><b>Erro ao montar a página.</b><pre>' + esc(e.stack || e) + "</pre></div>";
    }
    document.title = (item ? item.t + " · " : "") + D.projeto.titulo + " · " + D.projeto.cliente;
  }
  montarMenu();
  window.addEventListener("hashchange", rota);
  var tmr;
  document.getElementById("busca").addEventListener("input", function (e) {
    clearTimeout(tmr); var v = e.target.value;
    tmr = setTimeout(function () { location.hash = v.trim().length >= 2 ? "#busca/" + encodeURIComponent(v) : "#docs"; }, 300);
  });
  var bm = document.getElementById("botaoMenu");
  bm.addEventListener("click", function () { var m = document.getElementById("menu"); m.classList.toggle("aberto"); bm.setAttribute("aria-expanded", m.classList.contains("aberto")); });
  rota();
})();

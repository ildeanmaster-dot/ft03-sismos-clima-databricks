#!/usr/bin/env python3
"""Gera portal/index.html: o portal do projeto, num único arquivo que abre offline.

Tudo vem do repositório; nada é digitado à mão no portal:
  - documentos Markdown de docs/ (+ README, CHANGELOG)  -> páginas, tabelas e painéis
  - src/flows/manifest.json + definitions/*.json          -> um diagrama por fluxo (gerado das ações reais; opcional)
  - portal/dados/portal.json                               -> nome, cliente, cores, logo e caminhos
  - portal/dados/licenciamento.json                        -> preços oficiais e cenários de licença
Uso: python portal/gerar_portal.py   (só biblioteca padrão do Python 3.8+)
Para outro projeto: copiar a pasta portal/, ajustar portal/dados/*.json (inclusive o "menu": seções do portal,
com páginas genéricas {"id","t","doc","sub"} para qualquer documento) e rodar.
"""
import base64, datetime, glob, json, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, ".."))


def ler(rel, padrao=None):
    p = os.path.join(RAIZ, rel)
    if not os.path.exists(p):
        if padrao is not None:
            return padrao
        raise FileNotFoundError(rel)
    return open(p, encoding="utf-8").read()


def jload(rel):
    return json.loads(ler(rel))


# ---------------------------------------------------------------- Markdown: títulos e tabelas
def titulo_md(md, padrao):
    m = re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else padrao


def versao_md(md):
    m = re.search(r"^>\s*(Versão[^·\n]*·\s*[0-9/]+)", md, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^>\s*(Atualizado em [0-9/]+)", md, re.M)
    return m.group(1).strip() if m else ""


def limpar(c):
    c = re.sub(r"\*\*(.+?)\*\*", r"\1", c)
    c = re.sub(r"`([^`]*)`", r"\1", c)
    return c.strip()


def tabelas(md):
    """Lista de tabelas: {'secao': título ## acima, 'cab': [...], 'linhas': [[...]]}."""
    out, secao, linhas = [], "", md.split("\n")
    i = 0
    while i < len(linhas):
        l = linhas[i]
        if l.startswith("## "):
            secao = l[3:].strip()
        if l.startswith("|") and i + 1 < len(linhas) and re.match(r"^\|[\s:|-]+\|\s*$", linhas[i + 1]):
            cab = [c.strip() for c in l.strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(linhas) and linhas[j].startswith("|"):
                rows.append([c.strip() for c in linhas[j].strip().strip("|").split("|")])
                j += 1
            out.append({"secao": secao, "cab": cab, "linhas": rows})
            i = j
            continue
        i += 1
    return out


def linhas_com_id(md, prefixo):
    res = []
    for t in tabelas(md):
        for r in t["linhas"]:
            if r and re.match(rf"^\**{prefixo}", r[0]):
                res.append({"secao": t["secao"], "cab": t["cab"], "valores": r})
    return res


def status_base(s):
    s = limpar(s)
    for k in ["Não implementado", "Implementado", "Provisório", "Parcial", "Pendente", "Esqueleto", "Processo", "Informativo",
              "Resolvido", "Mitigado", "Aceito", "Aberto", "Aguarda", "Testado"]:
        if s.startswith(k):
            return k
    return "Outro"


# ---------------------------------------------------------------- Fluxos: diagrama Mermaid a partir da definição
TIPO_ROTULO = {
    "InitializeVariable": "Variável", "SetVariable": "Definir variável", "IncrementVariable": "Somar variável",
    "AppendToArrayVariable": "Acrescentar à lista", "Compose": "Compor", "Query": "Filtrar matriz", "Select": "Selecionar",
    "Http": "HTTP", "Response": "Responder ao fluxo pai", "Terminate": "Encerrar", "Workflow": "Executar fluxo filho",
    "Scope": "Escopo", "If": "Condição", "Switch": "Alternar", "Foreach": "Aplicar a cada", "Until": "Repetir até",
    "AppendToStringVariable": "Acrescentar ao texto", "ParseJson": "Analisar JSON", "Wait": "Atraso",
}
CONECTOR = {"shared_sharepointonline": "SharePoint", "shared_commondataserviceforapps": "Dataverse", "shared_teams": "Teams",
            "shared_office365": "Outlook", "shared_office365users": "Usuários do Office 365",
            "shared_excelonlinebusiness": "Excel Online (Business)", "shared_approvals": "Aprovações"}
# Conectores padrão (Standard) que não têm classe própria no diagrama
PADRAO = ("shared_office365", "shared_office365users", "shared_excelonlinebusiness", "shared_approvals")
CONEXAO = ("OpenApiConnection", "OpenApiConnectionWebhook")


def rot(nome):
    return nome.replace("_", " ")


def esc(s):
    return s.replace('"', "#quot;").replace("<", "#lt;").replace(">", "#gt;")


class Diagrama:
    def __init__(self, codigo):
        self.n = 0
        self.ids = {}
        self.linhas = []
        self.classes = {}
        self.codigo = codigo.replace("-", "")

    def nid(self, nome):
        if nome not in self.ids:
            self.n += 1
            self.ids[nome] = f"{self.codigo}n{self.n}"
        return self.ids[nome]

    def classe(self, a):
        t = a.get("type")
        if t in CONEXAO:
            api = a["inputs"]["host"]["apiId"].split("/")[-1]
            if api in PADRAO:
                return "std"
            return {"shared_sharepointonline": "sp", "shared_commondataserviceforapps": "prem", "shared_teams": "teams"}.get(api, "prem")
        if t == "Http":
            return "prem"
        if t in ("Response", "Terminate"):
            return "fim"
        if t == "Workflow":
            return "filho"
        return "ctl"

    def rotulo(self, nome, a):
        t = a.get("type")
        if t in CONEXAO:
            h = a["inputs"]["host"]
            sub = f"{CONECTOR.get(h['apiId'].split('/')[-1], h['apiId'].split('/')[-1])} · {h['operationId']}"
        elif t == "Http":
            sub = f"HTTP {a['inputs'].get('method', '')}"
        else:
            sub = TIPO_ROTULO.get(t, t)
        return f'"{esc(rot(nome))}<br/><small>{esc(sub)}</small>"'

    def bloco(self, acoes, ind="  "):
        """Desenha um conjunto de ações irmãs e as ligações runAfter entre elas."""
        for nome, a in acoes.items():
            t = a.get("type")
            i = self.nid(nome)
            if t in ("Scope", "If", "Switch", "Foreach", "Until"):
                cab = TIPO_ROTULO.get(t, t)
                extra = ""
                if t == "Foreach":
                    extra = " (paralelo)" if a.get("runtimeConfiguration", {}).get("concurrency", {}).get("repetitions", 1) > 1 else ""
                self.linhas.append(f'{ind}subgraph {i}["{esc(cab)}: {esc(rot(nome))}{extra}"]')
                self.linhas.append(f"{ind}  direction TB")
                if t == "If":
                    si, nao = self.nid(nome + "#sim"), self.nid(nome + "#nao")
                    self.linhas.append(f'{ind}  subgraph {si}["Sim"]')
                    self.linhas.append(f"{ind}    direction TB")
                    self.bloco(a.get("actions", {}), ind + "    ")
                    if not a.get("actions"):
                        self.linhas.append(f'{ind}    {si}v["(nada)"]:::vazio')
                    self.linhas.append(f"{ind}  end")
                    self.linhas.append(f'{ind}  subgraph {nao}["Não"]')
                    self.linhas.append(f"{ind}    direction TB")
                    els = a.get("else", {}).get("actions", {})
                    self.bloco(els, ind + "    ")
                    if not els:
                        self.linhas.append(f'{ind}    {nao}v["(nada)"]:::vazio')
                    self.linhas.append(f"{ind}  end")
                elif t == "Switch":
                    for cnome, c in a.get("cases", {}).items():
                        ci = self.nid(nome + "#c#" + cnome)
                        self.linhas.append(f'{ind}  subgraph {ci}["Caso {esc(c.get("case", cnome))}"]')
                        self.linhas.append(f"{ind}    direction TB")
                        self.bloco(c.get("actions", {}), ind + "    ")
                        self.linhas.append(f"{ind}  end")
                    if a.get("default", {}).get("actions"):
                        di = self.nid(nome + "#padrao")
                        self.linhas.append(f'{ind}  subgraph {di}["Padrão"]')
                        self.linhas.append(f"{ind}    direction TB")
                        self.bloco(a["default"]["actions"], ind + "    ")
                        self.linhas.append(f"{ind}  end")
                else:
                    self.bloco(a.get("actions", {}), ind + "  ")
                self.linhas.append(f"{ind}end")
            else:
                self.linhas.append(f"{ind}{i}[{self.rotulo(nome, a)}]:::{self.classe(a)}")
        for nome, a in acoes.items():
            for dep, sts in a.get("runAfter", {}).items():
                if dep in self.ids:
                    lab = "" if sts == ["Succeeded"] else "|" + esc(", ".join({"Succeeded": "sucesso", "Failed": "falha", "Skipped": "ignorado", "TimedOut": "tempo esgotado"}.get(s, s) for s in sts)) + "|"
                    seta = "-->" if sts == ["Succeeded"] else "-.->"
                    self.linhas.append(f"{ind}{self.ids[dep]} {seta}{lab} {self.ids[nome]}")

    def gerar(self, d):
        trig_nome, trig = list(d["triggers"].items())[0]
        self.linhas = ["flowchart TB"]
        ti = self.nid("__gatilho__")
        self.linhas.append(f'  {ti}(["{esc(gatilho_texto(trig_nome, trig))}"]):::gat')
        self.bloco(d["actions"])
        raizes = [n for n, a in d["actions"].items() if not a.get("runAfter")]
        for r in raizes:
            self.linhas.append(f"  {ti} --> {self.ids[r]}")
        self.linhas += [
            "  classDef gat fill:#242424,color:#FFFFFF,stroke:#242424",
            "  classDef sp fill:#FFFFFF,stroke:#5CACEB,color:#242424",
            "  classDef prem fill:#F4F2FB,stroke:#57479C,color:#242424",
            "  classDef teams fill:#FFFFFF,stroke:#8F7ED7,color:#242424",
            "  classDef filho fill:#E6E2F5,stroke:#57479C,color:#242424",
            "  classDef fim fill:#FFFFFF,stroke:#D43416,color:#242424",
            "  classDef ctl fill:#FFFFFF,stroke:#ACB0BC,color:#242424",
            "  classDef std fill:#FFFFFF,stroke:#687FA4,color:#242424",
            "  classDef vazio fill:#F2F2F2,stroke:#D2D6E0,color:#5C5C5C",
        ]
        return "\n".join(self.linhas)


def gatilho_texto(nome, t):
    tp = t.get("type")
    if tp == "Recurrence":
        r = t["recurrence"]
        s = r.get("schedule", {})
        freq = {"Hour": "hora", "Day": "dia", "Week": "semana", "Minute": "minuto"}.get(r["frequency"], r["frequency"])
        txt = f"Recorrência: a cada {r['interval']} {freq}"
        if s.get("hours"):
            hh = f"{int(s['hours'][0]):02d}:{int(s.get('minutes', [0])[0]):02d}"
            dias = ", ".join(s.get("weekDays", []))
            txt += f" às {hh}" + (f" ({dias})" if dias else "")
        return txt
    if tp == "Request":
        if t.get("kind") == "PowerAppV2":
            return "Chamado pelo Power Apps (V2)"
        return "Chamado por outro fluxo (filho)"
    if tp == "OpenApiConnection":
        op = t["inputs"]["host"]["operationId"]
        lista = t["inputs"]["parameters"].get("table", "")
        nome_op = {"GetOnNewItems": "Quando um item é criado", "GetOnUpdatedItems": "Quando um item é criado ou modificado"}.get(op, op)
        return f"SharePoint: {nome_op} em {lista}"
    return f"{tp}: {rot(nome)}"


def info_fluxo(code, meta, cd):
    d = cd["properties"]["definition"]
    acoes = []

    def walk(ac, pai=""):
        for n, a in ac.items():
            t = a.get("type")
            det = ""
            if t in CONEXAO:
                h = a["inputs"]["host"]
                det = f"{CONECTOR.get(h['apiId'].split('/')[-1], h['apiId'])} · {h['operationId']}"
                tb = a["inputs"].get("parameters", {}).get("table")
                if tb:
                    det += f" · {tb}"
            elif t == "Http":
                det = f"{a['inputs'].get('method', '')} {a['inputs'].get('uri', '')}"
            acoes.append({"nome": rot(n), "tipo": TIPO_ROTULO.get(t, "Conector" if t in CONEXAO else t),
                          "detalhe": det, "descricao": a.get("description", ""), "dentro": rot(pai)})
            walk(a.get("actions", {}), n)
            walk(a.get("else", {}).get("actions", {}), n)
            for c in a.get("cases", {}).values():
                walk(c.get("actions", {}), n)
            walk(a.get("default", {}).get("actions", {}), n)

    walk(d["actions"])
    trig_nome, trig = list(d["triggers"].items())[0]
    conns = sorted({CONECTOR.get(v["api"]["name"], v["api"]["name"]) for v in cd["properties"]["connectionReferences"].values()})
    if any(a["tipo"] == "HTTP" for a in acoes):
        conns.append("HTTP")
    premium = any(c in ("Dataverse", "HTTP") for c in conns)
    params = [k for k in d.get("parameters", {}) if not k.startswith("$")]
    return {
        "codigo": code, "nome": meta["name"], "descricao": meta.get("description", ""),
        "gatilho": gatilho_texto(trig_nome, trig),
        "gatilho_desc": trig.get("description", ""),
        "conexoes": conns, "premium": premium, "parametros": params,
        "acoes": acoes, "n_acoes": len(acoes),
        "pendentes": [a for a in acoes if "PENDENTE" in a["descricao"]],
        "mermaid": Diagrama(code).gerar(d),
    }


# ---------------------------------------------------------------- coleta
def coletar():
    cfg = jload("portal/dados/portal.json")
    lic = jload("portal/dados/licenciamento.json")
    F = cfg["fontes"]
    docs = []
    for pasta in cfg["pastas_docs"]:
        for p in sorted(glob.glob(os.path.join(RAIZ, pasta, "**", "*.md"), recursive=True)):
            rel = os.path.relpath(p, RAIZ).replace(os.sep, "/")
            if "/arquivo/" in rel:
                continue
            md = open(p, encoding="utf-8").read()
            docs.append({"caminho": rel, "grupo": cfg["rotulos_pastas"].get(pasta, pasta), "titulo": titulo_md(md, os.path.basename(p)),
                         "versao": versao_md(md), "md": md})
    for rel in cfg["arquivos_raiz"]:
        md = ler(rel, "")
        if md:
            docs.append({"caminho": rel, "grupo": "Raiz do projeto", "titulo": titulo_md(md, rel), "versao": versao_md(md), "md": md})

    md_reg, md_req, md_dt = ler(F["regras"]), ler(F["requisitos"]), ler(F["debito"])
    regras = []
    for r in linhas_com_id(md_reg, "RN-"):
        v, cab = r["valores"], r["cab"]
        st = v[cab.index("Status")] if "Status" in cab else ""
        regras.append({"id": limpar(v[0]), "area": re.sub(r"^\d+\.\s*", "", r["secao"]), "regra": v[1],
                       "origem": v[cab.index("Origem")] if "Origem" in cab else (v[cab.index("Para quem")] if "Para quem" in cab else ""),
                       "status": st, "status_base": status_base(st),
                       "onde": v[cab.index("Onde está")] if "Onde está" in cab else (v[cab.index("Canal")] if "Canal" in cab else "")})
    reqs = []
    for r in linhas_com_id(md_req, "RN?F-"):
        v, cab = r["valores"], r["cab"]
        st = v[cab.index("Status")] if "Status" in cab else ""
        reqs.append({"id": limpar(v[0]), "tipo": "Funcional" if v[0].startswith("RF") else "Não funcional", "texto": v[1],
                     "prioridade": v[cab.index("Prior.")] if "Prior." in cab else "", "status": st, "status_base": status_base(st)})
    debitos = []
    for r in linhas_com_id(md_dt, "DT-"):
        v, cab = r["valores"], r["cab"]
        g = lambda k: v[cab.index(k)] if k in cab else ""
        debitos.append({"id": v[0], "texto": g("Débito"), "impacto": g("Impacto"), "tipo": g("Tipo"), "prioridade": g("Prioridade"),
                        "acao": g("Ação"), "depende": g("Depende de"), "status": g("Status"), "status_base": status_base(g("Status"))})
    md_dec = ler(F["decisoes"])
    pend = [{"id": limpar(r["valores"][0]), "texto": r["valores"][1], "bloqueia": r["valores"][2], "com": r["valores"][3]}
            for r in linhas_com_id(md_dec, r"\**P-?\d") if r["secao"].startswith("2.")]
    decis = [{"id": limpar(r["valores"][0]), "texto": r["valores"][1], "data": r["valores"][2], "situacao": r["valores"][3]}
             for r in linhas_com_id(md_dec, r"\**D-?\d") if r["secao"].startswith("1.")]

    md_est = ler(F["estado"])
    tbs = tabelas(md_est)
    etapas = next((t for t in tbs if t["cab"][:2] == ["Etapa", "Situação"]), {"linhas": []})["linhas"]
    componentes = next((t for t in tbs if t["cab"][:2] == ["Componente", "Situação"]), {"linhas": []})["linhas"]
    proximos = next((t for t in tbs if t["cab"][:2] == ["#", "Ação"]), {"linhas": []})["linhas"]

    # Fluxos Power Automate: opcionais (projeto sem código ainda não tem manifesto)
    estado_fl = {}
    md_fl = ler(F["fluxos_doc"], "") if F.get("fluxos_doc") else ""
    for t in tabelas(md_fl):
        if t["cab"][:2] == ["Fluxo", "Estado"]:
            for r in t["linhas"]:
                estado_fl[r[0].split(" ")[0]] = {"estado": limpar(r[1]), "teste": r[2], "motivo": r[3] if len(r) > 3 else ""}
    fluxos = []
    if F.get("manifesto_fluxos") and os.path.exists(os.path.join(RAIZ, F["manifesto_fluxos"])):
        man = jload(F["manifesto_fluxos"])
        for meta in sorted(man["flows"], key=lambda f: f["code"]):
            cd = jload(os.path.join(F["pasta_fluxos"], meta["file"]).replace(os.sep, "/"))
            fi = info_fluxo(meta["code"], meta, cd)
            fi.update(estado_fl.get(meta["code"], {"estado": "", "teste": "", "motivo": ""}))
            fluxos.append(fi)

    diagramas = []
    for chave in ("arquitetura", "diagramas"):
        md = ler(F[chave])
        for m in re.finditer(r"^## (.+?)\n((?:(?!^## ).)*?)```mermaid\n(.*?)```", md, re.S | re.M):
            texto = re.sub(r"```.*", "", m.group(2), flags=re.S).strip()
            diagramas.append({"titulo": re.sub(r"^\d+\.\s*", "", m.group(1).strip()), "fonte": F[chave], "texto": texto, "mermaid": m.group(3)})
    fluxogramas = []
    for f in F.get("fluxogramas", []):
        svg = ler(f["arquivo"], "")
        if not svg:
            continue
        svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
        lab = re.search(r'aria-label="([^"]*)"', svg)
        fluxogramas.append({"titulo": f.get("titulo") or (lab.group(1) if lab else f["arquivo"]), "arquivo": f["arquivo"],
                            "src": "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()})

    md_log = ler(F["changelog"])
    historico = []
    for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", md_log, re.S | re.M):
        historico.append({"titulo": m.group(1).strip(), "itens": [limpar(x[2:]) for x in m.group(2).strip().split("\n") if x.startswith("- ")]})

    logo = ler(cfg["logo"], "")
    logo = re.sub(r"<metadata>.*?</metadata>", "", logo, flags=re.S)
    logo_src = "data:image/svg+xml;base64," + base64.b64encode(logo.encode("utf-8")).decode() if logo else ""

    return {
        "projeto": {k: cfg[k] for k in ("titulo", "cliente", "fornecedor", "subtitulo")},
        "menu": cfg.get("menu"), "painel": cfg.get("painel", {}),
        "gerado_em": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "logo": logo_src, "cores": cfg["cores"], "fonte": cfg["fonte"], "fontes": F,
        "docs": docs, "regras": regras, "requisitos": reqs, "debitos": debitos, "pendencias": pend, "decisoes": decis,
        "etapas": etapas, "componentes": componentes, "proximos": proximos,
        "fluxos": fluxos, "diagramas": diagramas, "fluxogramas": fluxogramas, "historico": historico, "licenciamento": lic,
    }


def main():
    dados = coletar()
    modelo = ler("portal/modelo/portal.html")
    css = ler("portal/modelo/portal.css")
    js = ler("portal/modelo/portal.js")
    marked = ler("portal/vendor/marked.min.js")
    mermaid = ler("portal/vendor/mermaid.min.js")
    cores = "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in dados["cores"].items())
    css = css.replace("/*CORES*/", cores).replace("/*FONTE*/", dados["fonte"])
    blob = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = (modelo.replace("{{TITULO}}", f"{dados['projeto']['titulo']} · {dados['projeto']['cliente']}")
                  .replace("/*{{CSS}}*/", css)
                  .replace("/*{{MARKED}}*/", marked.replace("</script", "<\\/script"))
                  .replace("/*{{MERMAID}}*/", mermaid.replace("</script", "<\\/script"))
                  .replace("{{DADOS}}", blob)
                  .replace("/*{{JS}}*/", js))
    saida = os.path.join(AQUI, "index.html")
    open(saida, "w", encoding="utf-8").write(html)
    print(f"{saida}: {len(html) // 1024} KB · {len(dados['docs'])} documentos · {len(dados['regras'])} regras · "
          f"{len(dados['requisitos'])} requisitos · {len(dados['debitos'])} débitos · {len(dados['fluxos'])} fluxos · "
          f"{len(dados['diagramas'])} diagramas · {len(dados['fluxogramas'])} fluxogramas")


if __name__ == "__main__":
    main()

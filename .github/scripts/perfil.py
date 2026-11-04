"""Gera o conteúdo dinâmico do perfil: imagens, selos e blocos do README.

Imagens e selos vão para a pasta de saída, que o workflow publica na branch
"output". O texto do README é editado à mão, exceto os blocos entre os
marcadores <!-- auto:nome --> e <!-- /auto:nome -->, reescritos com --readme a
partir de curriculo.py e da lista de repositórios. O workflow só commita na
main quando o conteúdo de um bloco realmente muda.

Uso:
    python .github/scripts/perfil.py                   # tema do dia
    python .github/scripts/perfil.py --tema natal      # força um tema
    python .github/scripts/perfil.py --data 2026-12-25 # simula uma data
    python .github/scripts/perfil.py --offline         # não acessa a API
    python .github/scripts/perfil.py --readme          # reescreve os blocos do README
    python .github/scripts/perfil.py --listar          # calendário de temas
    python .github/scripts/perfil.py --saida dist      # pasta de saída (padrão)

Usa apenas a biblioteca padrão. GITHUB_TOKEN é opcional localmente, mas no
Actions evita o limite de requisições e libera o calendário via GraphQL.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import curriculo
from animacoes import emblema_stl, linha_do_tempo, odometro, radar, relogio, terminal
from banner import banner
from estilo import APAGADO, FONTE, FUNDO, TEXTO, esc, moldura, numero
from temas import PADRAO, TEMAS, Tema, legivel, luminancia, misturar, tema_do_dia

USUARIO = "GuiiBM"
RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "dist"
LINKS = f"https://raw.githubusercontent.com/{USUARIO}/MyPersonalLinks/HEAD/links.json"
BRASILIA = timezone(timedelta(hours=-3))

# Textos do banner do topo.
NOME = "Guilherme Batistela"
COMANDO = "root@guiibm:~$ whoami"
CHIPS = ["ADS @ Fatec", "Pesquisador PIBICT", "Red Team", "Linux Mint"]

# Seções do README: cada uma tem um divisor animado (secoes/01.svg, 02.svg...)
# que mostra o avanço na página.
TOTAL_SECOES = 12

# Linhas do texto digitado abaixo do banner (a saudação do tema entra antes).
DIGITANDO = [
    ">_  Offensive Security Enthusiast",
    ">_  Future Red Teamer 🎯",
    ">_  Web Development & Low-Level Coding",
    ">_  Focus: Pentesting & Security Research",
]
BOOT = [
    "[OK] Loading kernel modules...",
    "[OK] Establishing encrypted tunnel...",
    "[WARN] Unauthorized access attempt blocked",
    f"[OK] ACCESS GRANTED // WELCOME, {USUARIO}",
]

# Selos do README (selos/<arquivo>.json, lidos pelo shields.io): mensagem,
# logo do Simple Icons e qual cor do tema usar.
SELOS = [
    ("portfolio", "Portfólio", "netlify", "c1"),
    ("links", "Links", "linktree", "c2"),
    ("red_team", "Red Team", "kalilinux", "c1"),
    ("web_security", "Web App Security", "burpsuite", "c2"),
    ("network_recon", "Network Recon", "wireguard", "acento"),
    ("traffic", "Traffic Analysis", "wireshark", "c2"),
    ("osint", "OSINT", "searxng", "acento"),
    ("automacao", "Automação", "gnubash", "c1"),
    ("ver_portfolio", "⚡ Ver portfólio completo", None, "c1"),
]

# Números da seção de métricas (selos/<chave>.json): chave em dados["stats"],
# rótulo e cor do tema. Como selo, o número muda sem nenhum commit na main.
METRICAS = [
    ("contribuicoes", "contribuições", "c1"),
    ("commits", "commits", "c2"),
    ("prs", "pull requests", "c1"),
    ("issues", "issues", "c2"),
    ("repos", "repositórios", "c1"),
    ("estrelas", "estrelas", "c2"),
    ("seq_atual", "sequência atual", "c1"),
    ("seq_maior", "recorde", "c2"),
]
EM_DIAS = {"seq_atual", "seq_maior"}

# Medalha de cada nível de prêmio em curriculo.PREMIOS.
MEDALHAS = {"ouro": "🥇", "prata": "🎖️", "bronze": "🥉", "marca": "✨"}

# Quantidade de linhas da lista de projetos.
TOTAL_REPOS = 6
# Repositórios que não devem aparecer em "Repositórios recentes".
REPOS_IGNORADOS = {USUARIO}
# Descrições que têm prioridade sobre a do GitHub. Sem nenhuma das duas, vale o
# primeiro parágrafo do README e, depois, a descrição do index.html.
DESCRICOES: dict[str, str] = {
    "Verto-Multi-purpose-Media-Security-Processing-Suite":
        "Suíte local-first com 40 ferramentas de IA, criptografia, binários e mídia.",
    "Massive-OSINT-Communication-Framework":
        "Coleta de dados públicos (OSINT) e automação de comunicação via WhatsApp Web.",
}

CITACOES = [
    ("Security is not a product, but a process.", "Bruce Schneier"),
    ("Amateurs hack systems, people hack people.", "Bruce Schneier"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Given enough eyeballs, all bugs are shallow.", "Eric S. Raymond"),
    ("There are only two types of companies: those that have been hacked "
     "and those that will be.", "Robert Mueller"),
    ("Passwords are like underwear: don't let people see it, change it very "
     "often, and you shouldn't share it with strangers.", "Chris Pirillo"),
    ("If you think technology can solve your security problems, then you "
     "don't understand the problems and you don't understand the "
     "technology.", "Bruce Schneier"),
]

CORES_LINGUAGENS = {
    "Python": "3572A5", "PHP": "4F5D95", "HTML": "e34c26", "CSS": "663399",
    "JavaScript": "f1e05a", "TypeScript": "3178c6", "C": "555555",
    "C++": "f34b7d", "C#": "178600", "Shell": "89e051", "Java": "b07219",
    "Dart": "00B4AB", "Go": "00ADD8", "Rust": "dea584", "Hack": "878787",
    "Blade": "f7523f", "Vue": "41b883", "Dockerfile": "384d54",
}

# Categorias do links.json (MyPersonalLinks), na ordem em que aparecem no README.
CATEGORIAS_SITES = {
    "Pessoal": "🧑‍💻 Projetos pessoais",
    "Website": "🏢 Sites para empresas e marcas",
    "Web Data Base": "🗄️ Sites com banco de dados",
    "Entertainment": "🎮 Entretenimento e utilidades",
}


# --------------------------------------------------------------------------
# Coleta de dados
# --------------------------------------------------------------------------

def requisitar(url: str, dados: dict | None = None) -> bytes:
    cabecalhos = {"User-Agent": f"{USUARIO}-perfil-dinamico"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        cabecalhos["Authorization"] = f"Bearer {token}"
    corpo = json.dumps(dados).encode() if dados is not None else None
    req = urllib.request.Request(url, data=corpo, headers=cabecalhos)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def api(caminho: str):
    return json.loads(requisitar(f"https://api.github.com{caminho}"))


def total_busca(tipo: str, consulta: str) -> int:
    q = urllib.parse.quote(consulta)
    return api(f"/search/{tipo}?q={q}&per_page=1")["total_count"]


def calendario() -> dict[date, int]:
    """Contribuições diárias do último ano."""
    if os.environ.get("GITHUB_TOKEN"):
        consulta = """query($u: String!) { user(login: $u) {
            contributionsCollection { contributionCalendar {
              weeks { contributionDays { date contributionCount } } } } } }"""
        resp = json.loads(requisitar("https://api.github.com/graphql",
                                     {"query": consulta, "variables": {"u": USUARIO}}))
        semanas = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return {date.fromisoformat(d["date"]): d["contributionCount"]
                for s in semanas for d in s["contributionDays"]}

    # Sem token: lê a página pública do calendário.
    pagina = requisitar(f"https://github.com/users/{USUARIO}/contributions").decode()
    datas = dict(re.findall(r'data-date="([\d-]+)" id="([^"]+)"', pagina))
    datas = {id_: d for d, id_ in datas.items()}
    dias = {}
    for id_, texto in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)', pagina):
        if id_ in datas:
            n = re.match(r"(\d+)", texto.strip())
            dias[date.fromisoformat(datas[id_])] = int(n.group(1)) if n else 0
    if not dias:
        raise ValueError("calendário de contribuições vazio")
    return dict(sorted(dias.items()))


def resumo_readme(repo: dict) -> str | None:
    """Primeiro parágrafo de texto do README, sem marcação."""
    url = f"https://raw.githubusercontent.com/{USUARIO}/{repo['name']}/HEAD/README.md"
    try:
        texto = requisitar(url).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return None
    em_codigo = False
    for linha in texto.splitlines():
        linha = linha.strip()
        if linha.startswith("```"):
            em_codigo = not em_codigo
            continue
        if em_codigo or not linha or linha.startswith(("#", "<", "!", "[!", "|", "---", "***", "- ", "* ")):
            continue
        linha = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", linha.lstrip("> "))
        linha = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", linha)
        linha = re.sub(r"[*_`]", "", linha).strip()
        if len(linha) > 20:
            return linha
    return None


def resumo_site(repo: dict) -> str | None:
    """Descrição (ou título) do index.html, para repositórios de sites sem README."""
    url = f"https://raw.githubusercontent.com/{USUARIO}/{repo['name']}/HEAD/index.html"
    try:
        pagina = requisitar(url).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return None
    achado = (re.search(r"""<meta[^>]*name=["']description["'][^>]*content=(["'])(?P<texto>.*?)\1""", pagina, re.I | re.S)
              or re.search(r"<title[^>]*>(?P<texto>.*?)</title>", pagina, re.I | re.S))
    return html.unescape(achado["texto"]).strip() or None if achado else None


def horas_de_commit() -> list[int]:
    """Commits públicos mais recentes por hora do dia, no horário de Brasília."""
    q = urllib.parse.quote(f"author:{USUARIO}")
    horas = [0] * 24
    for item in api(f"/search/commits?q={q}&sort=author-date&order=desc&per_page=100")["items"]:
        horas[datetime.fromisoformat(item["commit"]["author"]["date"]).astimezone(BRASILIA).hour] += 1
    return horas


def sequencias(dias: dict[date, int], hoje: date) -> tuple[int, int]:
    """(sequência atual, maior sequência). Hoje sem commit não quebra a atual."""
    maior = corrente = 0
    for d in sorted(dias):
        corrente = corrente + 1 if dias[d] else 0
        maior = max(maior, corrente)
    atual, d = 0, hoje if dias.get(hoje) else hoje - timedelta(days=1)
    while dias.get(d):
        atual += 1
        d -= timedelta(days=1)
    return atual, maior


def coletar(hoje: date) -> dict:
    perfil = api(f"/users/{USUARIO}")
    repos = api(f"/users/{USUARIO}/repos?per_page=100&type=owner&sort=pushed")
    proprios = [r for r in repos if not r["fork"]]

    linguagens: dict[str, int] = {}
    for r in proprios:
        if r["name"] in REPOS_IGNORADOS:
            continue
        for nome, bytes_ in api(f"/repos/{USUARIO}/{r['name']}/languages").items():
            linguagens[nome] = linguagens.get(nome, 0) + bytes_

    dias = calendario()
    atual, maior = sequencias(dias, hoje)
    desde = (hoje - timedelta(days=365)).isoformat()
    todos = [r for r in proprios if r["name"] not in REPOS_IGNORADOS]
    for r in todos:
        r["resumo"] = DESCRICOES.get(r["name"]) or r["description"] or resumo_readme(r) or resumo_site(r)
    resumir = lambda r: {"nome": r["name"], "url": r["html_url"], "resumo": r["resumo"],
                         "linguagem": r["language"], "estrelas": r["stargazers_count"],
                         "atualizado": r["pushed_at"][:10]}
    return {
        "repos": [resumir(r) for r in todos if not r["archived"]][:TOTAL_REPOS],
        "todos": [resumir(r) for r in todos],
        "sites": json.loads(requisitar(LINKS)),
        "horas": horas_de_commit(),
        "linguagens": linguagens,
        "dias": {d.isoformat(): n for d, n in dias.items()},
        "stats": {
            "contribuicoes": sum(dias.values()),
            "commits": total_busca("commits", f"author:{USUARIO} author-date:>{desde}"),
            "prs": total_busca("issues", f"author:{USUARIO} type:pr created:>{desde}"),
            "issues": total_busca("issues", f"author:{USUARIO} type:issue created:>{desde}"),
            "repos": len(proprios),
            "estrelas": sum(r["stargazers_count"] for r in proprios),
            "seq_atual": atual,
            "seq_maior": maior,
            "seguidores": perfil["followers"],
        },
    }


# --------------------------------------------------------------------------
# Cards SVG
# --------------------------------------------------------------------------

def card_linguagens(t: Tema, linguagens: dict[str, int]) -> str:
    total = sum(linguagens.values()) or 1
    top = [(n, b) for n, b in sorted(linguagens.items(), key=lambda x: -x[1]) if b / total >= 0.001][:6]
    paleta = [legivel(t.c1), legivel(t.c2), t.acento]
    cores = [CORES_LINGUAGENS.get(n, paleta[i % 3]) for i, (n, _) in enumerate(top)]

    largura, x = 850, 25.0
    barras = []
    for (nome, b), cor in zip(top, cores):
        w = largura * b / total
        barras.append(f'<rect x="{x:.2f}" y="56" width="{max(w, 0.5):.2f}" height="10" fill="#{cor}"><title>{esc(nome)}</title></rect>')
        x += w
    barra = (f'  <clipPath id="barra"><rect x="25" y="56" width="{largura}" height="10" rx="5"/></clipPath>\n'
             f'  <g clip-path="url(#barra)" class="surge">{"".join(barras)}</g>')

    legenda = []
    for i, ((nome, b), cor) in enumerate(zip(top, cores)):
        linha, coluna = divmod(i, 3)
        lx, ly = 25 + coluna * 295, 100 + linha * 30
        legenda.append(
            f'  <g class="surge" style="animation-delay:{200 + i * 70}ms">'
            f'<circle cx="{lx + 5}" cy="{ly - 4.5}" r="5" fill="#{cor}"/>'
            f'<text x="{lx + 16}" y="{ly}" class="rotulo">{esc(nome)}</text>'
            f'<text x="{lx + 260}" y="{ly}" class="apagado" text-anchor="end">{100 * b / total:.1f}%</text></g>'
        )
    return moldura(t, 900, 100 + 30 * ((len(top) + 2) // 3), "Linguagens mais usadas", barra + "\n" + "\n".join(legenda))


def card_divisor(t: Tema, numero: int) -> str:
    """Linha fina e animada entre as seções: a parte cheia marca o avanço."""
    largura, altura, meio = 1000, 14, 7
    cheio = largura * numero / TOTAL_SECOES
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" aria-hidden="true">
  <style>
    .luz {{ animation: varrer 4s ease-in-out infinite; }}
    .pulso {{ animation: pulsar 2s ease-in-out infinite; transform-origin: {cheio - 7:.1f}px {meio}px; }}
    @keyframes varrer {{ from {{ transform: translateX(-160px); }} to {{ transform: translateX({cheio:.1f}px); }} }}
    @keyframes pulsar {{ 50% {{ transform: scale(1.5); opacity: .45; }} }}
    @media (prefers-reduced-motion: reduce) {{ .luz, .pulso {{ animation: none; }} .luz {{ display: none; }} }}
  </style>
  <defs>
    <linearGradient id="cheio" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#{c1}"/><stop offset="100%" stop-color="#{c2}"/></linearGradient>
    <linearGradient id="brilho" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#fff" stop-opacity="0"/><stop offset="50%" stop-color="#fff" stop-opacity=".75"/><stop offset="100%" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="parte"><rect y="{meio - 2}" width="{cheio:.1f}" height="4" rx="2"/></clipPath>
  </defs>
  <rect y="{meio - 2}" width="{largura}" height="4" rx="2" fill="#{c1}" fill-opacity=".18"/>
  <g clip-path="url(#parte)">
    <rect width="{cheio:.1f}" height="{altura}" fill="url(#cheio)"/>
    <rect width="160" height="{altura}" fill="url(#brilho)" class="luz"/>
  </g>
  <circle cx="{cheio - 7:.1f}" cy="{meio}" r="4.5" fill="#{acento}" class="pulso"/>
</svg>
"""


def card_atividade(t: Tema, dias: dict[date, int], hoje: date) -> str:
    periodo = [hoje - timedelta(days=i) for i in range(29, -1, -1)]
    valores = [dias.get(d, 0) for d in periodo]
    largura, altura = 900, 300
    esq, dir_, topo, base = 55, 25, 70, 250
    teto = max(max(valores), 4)
    teto += (-teto) % 4  # múltiplo de 4 para linhas de grade redondas
    passo = (largura - esq - dir_) / (len(valores) - 1)

    pontos = [(esq + i * passo, base - (base - topo) * v / teto) for i, v in enumerate(valores)]
    linha = " ".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    area = f"{esq},{base} {linha} {pontos[-1][0]:.1f},{base}"

    grade = []
    for k in range(5):
        y = base - (base - topo) * k / 4
        grade.append(f'  <line x1="{esq}" y1="{y:.1f}" x2="{largura - dir_}" y2="{y:.1f}" stroke="#{APAGADO}" stroke-opacity="0.15"/>'
                     f'<text x="{esq - 10}" y="{y + 4:.1f}" text-anchor="end" class="apagado">{teto * k // 4}</text>')
    for i, d in enumerate(periodo):
        if i % 3 == 0 or i == len(periodo) - 1:
            grade.append(f'  <text x="{esq + i * passo:.1f}" y="{base + 22}" text-anchor="middle" class="apagado">{d.day:02d}/{d.month:02d}</text>')

    ponto = legivel(t.c2)
    marcadores = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{4 if v else 2.5}" fill="#{ponto if v else FUNDO}" stroke="#{ponto}" stroke-width="1.5"><title>{d.day:02d}/{d.month:02d}: {v}</title></circle>'
        for (x, y), v, d in zip(pontos, valores, periodo)
    )
    total, melhor = sum(valores), max(valores)
    resumo = (f'  <text x="{largura - dir_}" y="38" text-anchor="end" class="apagado">'
              f'{total} contribuições no período · melhor dia: {melhor}</text>')
    corpo = f"""  <defs>
    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#{t.c1}" stop-opacity="0.55"/><stop offset="100%" stop-color="#{t.c1}" stop-opacity="0.02"/>
    </linearGradient>
    <clipPath id="revela"><rect x="0" y="0" width="{largura}" height="{altura}" class="anima"><animate attributeName="width" from="0" to="{largura}" dur="1.4s" fill="freeze"/></rect></clipPath>
  </defs>
{chr(10).join(grade)}
{resumo}
  <g clip-path="url(#revela)">
    <polygon points="{area}" fill="url(#area)"/>
    <polyline points="{linha}" fill="none" stroke="url(#grad)" stroke-width="2.5" stroke-linejoin="round"/>
    {marcadores}
  </g>"""
    return moldura(t, largura, altura, "Atividade nos últimos 30 dias", corpo)


def quebrar(texto: str, largura: int, linhas: int) -> list[str]:
    palavras, saida, atual = texto.split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > largura:
            saida.append(atual)
            atual = p
            if len(saida) == linhas:
                break
        else:
            atual = f"{atual} {p}".strip()
    else:
        saida.append(atual)
        return saida
    saida[-1] = saida[-1][: largura - 1].rstrip(" ,.;:") + "…"
    return saida


def ha_quanto(quando: date, hoje: date) -> str:
    dias = (hoje - quando).days
    if dias <= 0:
        return "hoje"
    if dias == 1:
        return "ontem"
    if dias < 45:
        return f"há {dias} dias"
    meses = round(dias / 30)
    return f"há {meses} meses" if meses < 12 else f"há {dias // 365} ano(s)"


def card_rodape(t: Tema, hoje: date, agora: datetime) -> str:
    citacao, autor = CITACOES[hoje.toordinal() % len(CITACOES)]
    linhas = quebrar(f"“{citacao}”", 80, 3)
    largura = 1000
    altura = 150 + 26 * len(linhas)

    def onda(base: int, amplitude: int) -> str:
        pontos = " ".join(f"T{x} {base}" for x in range(500, 2 * largura + 1, 250))
        return f"M0 0 L0 {base} Q125 {base + amplitude} 250 {base} {pontos} L{2 * largura} 0Z"

    texto = "".join(
        f'<text x="{largura / 2}" y="{108 + i * 26}" text-anchor="middle" '
        f'style="font:italic 500 18px {FONTE};fill:#{TEXTO}">{esc(l)}</text>'
        for i, l in enumerate(linhas))
    y = 108 + 26 * len(linhas)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="{esc(citacao)} ({esc(autor)})">
  <title>{esc(citacao)} ({esc(autor)})</title>
  <style>
    .onda {{ animation: correr 9s linear infinite; }}
    .onda.lenta {{ animation-duration: 15s; }}
    @keyframes correr {{ to {{ transform: translateX(-500px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .onda {{ animation: none; }} }}
  </style>
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      {"".join(f'<stop offset="{o}%" stop-color="#{legivel(c)}"/>' for o, c in t.stops())}
    </linearGradient>
    <clipPath id="card"><rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{largura}" height="{altura}" fill="#{FUNDO}"/>
    <path d="{onda(46, 26)}" fill="url(#grad)" opacity=".45" class="onda lenta"/>
    <path d="{onda(34, -22)}" fill="url(#grad)" class="onda"/>
  </g>
  <rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="14" fill="none" stroke="#{legivel(t.c1)}" stroke-opacity=".45"/>
  {texto}
  <text x="{largura / 2}" y="{y + 4}" text-anchor="middle" style="font:600 14px {FONTE};fill:#{legivel(t.acento)}">— {esc(autor)}</text>
  <text x="{largura / 2}" y="{y + 32}" text-anchor="middle" class="apagado" style="font:12px {FONTE};fill:#{APAGADO}">Atualizado em {agora:%d/%m/%Y às %H:%M} (horário de Brasília)</text>
</svg>
"""


# --------------------------------------------------------------------------
# Blocos de HTML real do README (o GitHub remove CSS e JavaScript, mas mantém
# tabelas, blocos expansíveis, links e <kbd>)
# --------------------------------------------------------------------------

def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    """As células já vêm em HTML; quem chama escapa o que for texto."""
    topo = "".join(f'<th align="left">{c}</th>' for c in cabecalho)
    corpo = "\n".join("  <tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas)
    return f"<table>\n  <tr>{topo}</tr>\n{corpo}\n</table>"


def etiqueta(texto: str) -> str:
    """<kbd> com espaços que não quebram, para o período ficar em uma linha só."""
    return f"<kbd>{esc(texto).replace(' ', chr(0xA0))}</kbd>"


def bloco_trajetoria() -> str:
    itens = []
    for i, (periodo, cargo, instituicao, vinculo, atividades) in enumerate(curriculo.EXPERIENCIA):
        aberto = " open" if i == 0 else ""
        lista = "\n".join(f"    <li>{esc(a)}</li>" for a in atividades)
        itens.append(f"<details{aberto}>\n"
                     f"  <summary>{etiqueta(periodo)} <b>{esc(cargo)}</b> · {esc(instituicao)}</summary>\n"
                     f"  <p><sub>{esc(vinculo)}</sub></p>\n"
                     f"  <ul>\n{lista}\n  </ul>\n"
                     "</details>")
    return "\n".join(itens)


def bloco_pesquisa() -> str:
    itens = []
    for i, (periodo, titulo, situacao, coordenacao, financiamento, descricao) in enumerate(curriculo.PESQUISA):
        aberto = " open" if i == 0 else ""
        itens.append(f"<details{aberto}>\n"
                     f"  <summary>{etiqueta(periodo)} <b>{esc(titulo)}</b></summary>\n"
                     f"  <p>{esc(descricao)}</p>\n"
                     f"  <p><sub><b>Situação:</b> {esc(situacao)} · <b>Coordenação:</b> {esc(coordenacao)} · "
                     f"<b>Financiamento:</b> {esc(financiamento)}</sub></p>\n"
                     "</details>")
    return "\n".join(itens)


def bloco_producao() -> str:
    return tabela(["Produção", "Tipo", "Ano"],
                  [[f"<b>{esc(titulo)}</b>", esc(tipo), etiqueta(ano)]
                   for ano, titulo, tipo in curriculo.PRODUCAO_TECNICA])


def bloco_formacao() -> str:
    return tabela(["Curso", "Instituição", "Período"],
                  [[f"<b>{esc(curso)}</b>", esc(instituicao), etiqueta(periodo)]
                   for periodo, curso, instituicao in curriculo.FORMACAO])


def bloco_cursos() -> str:
    grupos = []
    for i, (grupo, cursos) in enumerate(curriculo.CURSOS.items()):
        horas = sum(h or 0 for *_, h in cursos)
        total = f" · {horas}h" if horas else ""
        aberto = " open" if i == 0 else ""
        linhas = [[esc(nome), esc(instituicao), f"{h}h" if h else "—", etiqueta(ano)]
                  for ano, nome, instituicao, h in cursos]
        grupos.append(f"<details{aberto}>\n  <summary><b>{esc(grupo)}</b> <sub>{len(cursos)} cursos{total}</sub></summary>\n\n"
                      + tabela(["Curso", "Instituição", "Carga", "Ano"], linhas) + "\n</details>")
    return "\n".join(grupos)


def bloco_idiomas() -> str:
    return tabela(["Idioma", "Compreende", "Fala", "Lê", "Escreve"],
                  [[f"<b>{esc(idioma)}</b>", *map(esc, niveis)] for idioma, *niveis in curriculo.IDIOMAS])


def bloco_premios() -> str:
    return tabela(["", "Prêmio ou destaque", "Onde", "Ano"],
                  [[MEDALHAS[nivel], f"<b>{esc(titulo)}</b>", esc(detalhe), etiqueta(ano)]
                   for ano, titulo, detalhe, nivel in curriculo.PREMIOS])


def bloco_eventos() -> str:
    linhas = [[esc(evento), f"<code>{esc(tipo)}</code>", etiqueta(ano)] for ano, evento, tipo in curriculo.EVENTOS]
    return (f"<details>\n  <summary><b>Ver os {len(linhas)} eventos e olimpíadas</b></summary>\n\n"
            + tabela(["Evento", "Tipo", "Ano"], linhas) + "\n</details>")


def bloco_destaques() -> str:
    cartoes = []
    for titulo, repo, resumo, stack, site in curriculo.DESTAQUES:
        pilha = " ".join(f"<code>{esc(s)}</code>" for s in stack)
        links = [f'<a href="https://github.com/{USUARIO}/{esc(repo)}">Código</a>']
        if site:
            links.append(f'<a href="{esc(site)}">Site no ar</a>')
        cartoes.append(f'<td width="50%" valign="top"><h4>{esc(titulo)}</h4><p>{esc(resumo)}</p>'
                       f'<p>{pilha}</p><p>{" · ".join(links)}</p></td>')
    linhas = ["<tr>" + "".join(cartoes[i:i + 2]) + "</tr>" for i in range(0, len(cartoes), 2)]
    return "<table>\n" + "\n".join(linhas) + "\n</table>"


def url_selo(arquivo: str) -> str:
    origem = f"https://raw.githubusercontent.com/{USUARIO}/{USUARIO}/output/selos/{arquivo}.json"
    return "https://img.shields.io/endpoint?" + urllib.parse.urlencode({"url": origem, "style": "flat-square"})


def link_linguagem(linguagem: str | None) -> str:
    if not linguagem:
        return "—"
    filtro = urllib.parse.urlencode({"tab": "repositories", "language": linguagem.lower()})
    return f'<a href="https://github.com/{USUARIO}?{esc(filtro)}"><code>{esc(linguagem)}</code></a>'


def bloco_projetos(repos: list[dict]) -> str:
    """A idade do último commit fica num selo: muda sem precisar de commit na main."""
    linhas = []
    for r in repos:
        estrelas = f' <sub>★ {r["estrelas"]}</sub>' if r["estrelas"] else ""
        linhas.append([
            f'<a href="{esc(r["url"])}"><b>{esc(r["nome"])}</b></a>{estrelas}',
            esc(r["resumo"]) if r["resumo"] else "<sub>Sem descrição por enquanto.</sub>",
            link_linguagem(r["linguagem"]),
            f'<img src="{esc(url_selo("repo-" + r["nome"]))}" alt="Último commit" />',
        ])
    return tabela(["Projeto", "O que é", "Linguagem", "Último commit"], linhas)


def bloco_todos(repos: list[dict]) -> str:
    """Em ordem alfabética, para só mudar quando entra ou sai um repositório."""
    linhas = [[f'<a href="{esc(r["url"])}"><b>{esc(r["nome"])}</b></a>',
               esc(r["resumo"]) if r["resumo"] else "<sub>Sem descrição por enquanto.</sub>",
               link_linguagem(r["linguagem"])]
              for r in sorted(repos, key=lambda r: r["nome"].lower())]
    return (f"<details>\n  <summary><b>Ver todos os {len(linhas)} repositórios públicos</b></summary>\n\n"
            + tabela(["Repositório", "O que é", "Linguagem"], linhas) + "\n</details>")


def bloco_sites(sites: list[dict]) -> str:
    grupos = []
    for tag, nome in CATEGORIAS_SITES.items():
        do_grupo = [s for s in sites if s.get("tag") == tag]
        if not do_grupo:
            continue
        linhas = [[f'<a href="{esc(s["url"].strip())}"><b>{esc(s["label"])}</b></a>', esc(s["description"])] for s in do_grupo]
        aberto = " open" if not grupos else ""
        grupos.append(f"<details{aberto}>\n  <summary><b>{esc(nome)}</b> <sub>{len(do_grupo)}</sub></summary>\n\n"
                      + tabela(["Site", "O que é"], linhas) + "\n</details>")
    return "\n".join(grupos)


def bloco_servicos() -> str:
    return '<p align="center">\n' + "\n".join(f"  <kbd>{esc(s)}</kbd>" for s in curriculo.SERVICOS) + "\n</p>"


def bloco_perfis() -> str:
    return tabela(["Perfil", "Marca", "Trabalho"],
                  [[f'<a href="https://instagram.com/{esc(p)}"><code>@{esc(p)}</code></a>', esc(nome), esc(trabalho)]
                   for p, nome, trabalho in curriculo.PERFIS])


def bloco_emblema() -> str:
    return "```stl\n" + emblema_stl() + "\n```"


def atualizar_readme(blocos: dict[str, str]) -> None:
    caminho = RAIZ / "README.md"
    texto = caminho.read_text(encoding="utf-8")
    for nome, conteudo in blocos.items():
        padrao = re.compile(rf"(<!-- auto:{nome} -->\n).*?(<!-- /auto:{nome} -->)", re.S)
        texto, trocas = padrao.subn(lambda m: f"{m[1]}{conteudo}\n{m[2]}", texto)
        if not trocas:
            print(f"Aviso: marcadores do bloco '{nome}' não encontrados no README.", file=sys.stderr)
    caminho.write_text(texto, encoding="utf-8")


# --------------------------------------------------------------------------
# Imagens de serviços externos, recoloridas com o tema
# --------------------------------------------------------------------------

def visivel(cor: str, alternativa: str) -> str:
    """Troca cores quase brancas, que somem no modo claro do GitHub."""
    return legivel(alternativa if luminancia(cor) > 200 else cor)


def selo(mensagem: str, cor: str, logo: str | None = None, rotulo: str = "") -> str:
    dados = {"schemaVersion": 1, "label": rotulo, "message": mensagem,
             "color": cor, "cacheSeconds": 300}
    if logo:
        dados |= {"namedLogo": logo, "logoColor": "0d1117" if luminancia(cor) > 170 else "white"}
    return json.dumps(dados, ensure_ascii=False) + "\n"


def baixar_svg(destino: Path, url: str) -> None:
    """Baixa um SVG; se o serviço falhar, mantém a versão publicada antes."""
    anterior = f"https://raw.githubusercontent.com/{USUARIO}/{USUARIO}/output/{destino.name}"
    for origem in (url, anterior):
        try:
            conteudo = requisitar(origem)
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
        if b"<svg" in conteudo[:4000]:
            destino.write_bytes(conteudo)
            return
    print(f"Aviso: não foi possível baixar {destino.name}.", file=sys.stderr)


def digitando(linhas: list[str], cor: str, **opcoes) -> str:
    parametros = {"center": "true", "vCenter": "true", "color": cor, **opcoes, "lines": ";".join(linhas)}
    return "https://readme-typing-svg.demolab.com/?" + urllib.parse.urlencode(
        parametros, quote_via=urllib.parse.quote, safe=";")


def externos(t: Tema, saida: Path, ano_novo: int) -> None:
    linhas = ([t.saudacao.format(ano_novo=ano_novo)] if t.saudacao else []) + DIGITANDO
    baixar_svg(saida / "digitando.svg", digitando(
        linhas, legivel(t.acento), font="Fira Code", weight=600, size=20, pause=1000, width=650, height=45))
    baixar_svg(saida / "boot.svg", digitando(
        BOOT, visivel(t.c2, t.c1), font="JetBrains Mono", weight=500, size=14, duration=2200,
        pause=400, width=600, height=90))
    for arquivo, tema_trofeu in (("trofeus.svg", t.trofeu), ("trofeus-claro.svg", "flat")):
        baixar_svg(saida / arquivo, "https://github-profile-trophies.vercel.app/?" + urllib.parse.urlencode(
            {"username": USUARIO, "theme": tema_trofeu, "column": -1, "rank": "-?", "margin-w": 12,
             "margin-h": 12, "no-bg": "true", "no-frame": "true"}))


# --------------------------------------------------------------------------

def escrever_saida(t: Tema) -> None:
    """Exporta as cores do tema para os próximos passos do workflow."""
    destino = os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    claro, escuro = "ebedf0", "161b22"
    niveis = (0.45, 0.65, 0.85, 1.0)
    cheio = legivel(t.c1)
    dots = lambda vazio: ",".join(["#" + vazio] + ["#" + misturar(vazio, cheio, f) for f in niveis])
    with open(destino, "a", encoding="utf-8") as f:
        f.write(f"tema={t.chave}\n")
        f.write(f"nome={t.nome}\n")
        f.write(f"perfil3d={t.perfil3d}\n")
        f.write(f"cobra=#{legivel(t.c2)}\n")
        f.write(f"cobra_clara=#{visivel(t.c2, t.c1)}\n")
        f.write(f"pontos_claro={dots(claro)}\n")
        f.write(f"pontos_escuro={dots(escuro)}\n")


def listar(ano: int) -> None:
    linhas = sorted((i, f, t) for t in TEMAS for i, f in t.periodos(ano) if i.year == ano)
    for i, f, t in linhas:
        intervalo = f"{i:%d/%m}" if i == f else f"{i:%d/%m} a {f:%d/%m}"
        print(f"{intervalo:<16} {t.emoji}  {t.nome}  [{t.chave}, prioridade {t.prioridade}]")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tema", help="força um tema pela chave (ex.: natal, halloween, padrao)")
    p.add_argument("--data", help="simula a data de hoje (AAAA-MM-DD)")
    p.add_argument("--offline", action="store_true", help="não acessa a API; usa os dados do cache")
    p.add_argument("--listar", action="store_true", help="lista o calendário de temas do ano")
    p.add_argument("--saida", type=Path, default=SAIDA, help="pasta onde as imagens são gravadas")
    p.add_argument("--readme", action="store_true", help="reescreve os blocos automáticos do README.md")
    args = p.parse_args()

    agora = datetime.now(BRASILIA)
    hoje = date.fromisoformat(args.data) if args.data else agora.date()
    if args.listar:
        listar(hoje.year)
        return 0

    if args.tema:
        temas = {t.chave: t for t in [PADRAO, *TEMAS]}
        if args.tema not in temas:
            print(f"Tema desconhecido: {args.tema}. Opções: {', '.join(temas)}", file=sys.stderr)
            return 2
        tema = temas[args.tema]
    else:
        tema = tema_do_dia(hoje)
    print(f"Tema: {tema.emoji} {tema.nome} ({tema.chave})")

    saida: Path = args.saida
    (saida / "secoes").mkdir(parents=True, exist_ok=True)
    (saida / "selos").mkdir(exist_ok=True)
    gravar = lambda nome, conteudo: (saida / nome).write_text(conteudo, encoding="utf-8")

    ano_novo = hoje.year + 1 if hoje.month == 12 else hoje.year
    subtitulo = tema.descricao.format(ano_novo=ano_novo).replace(" | ", " · ")
    gravar("rodape.svg", card_rodape(tema, hoje, agora))
    for i in range(1, TOTAL_SECOES + 1):
        gravar(f"secoes/{i:02d}.svg", card_divisor(tema, i))
    for arquivo, mensagem, logo, cor in SELOS:
        gravar(f"selos/{arquivo}.json", selo(mensagem, getattr(tema, cor), logo))
    if not args.offline:
        externos(tema, saida, ano_novo)

    # Os dados coletados ficam em cache (dados.json, publicado junto com as
    # imagens): se a API falhar, os cards usam os números da última coleta.
    cache = saida / "dados.json"
    dados = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else None
    if not args.offline:
        try:
            dados = coletar(hoje)
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as erro:
            print(f"Aviso: não foi possível coletar os dados ({erro}).", file=sys.stderr)
        else:
            cache.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    gravar("banner.svg", banner(tema, hoje, NOME, subtitulo, COMANDO, CHIPS))

    gravar("linha-do-tempo.svg", linha_do_tempo(tema, hoje))
    blocos = {"trajetoria": bloco_trajetoria(), "pesquisa": bloco_pesquisa(), "producao": bloco_producao(),
              "formacao": bloco_formacao(), "cursos": bloco_cursos(), "idiomas": bloco_idiomas(),
              "premios": bloco_premios(), "eventos": bloco_eventos(), "destaques": bloco_destaques(),
              "servicos": bloco_servicos(), "perfis": bloco_perfis(), "emblema": bloco_emblema()}
    if dados:
        dias = {date.fromisoformat(d): n for d, n in dados["dias"].items()}
        s = dados["stats"]
        gravar("linguagens.svg", card_linguagens(tema, dados["linguagens"]))
        gravar("atividade.svg", card_atividade(tema, dias, hoje))
        gravar("terminal.svg", terminal(tema, dados, hoje))
        gravar("odometro.svg", odometro(tema, [
            (s["contribuicoes"], "", "contribuições em 12 meses"), (s["repos"], "", "repositórios públicos"),
            (curriculo.PROJETOS_ENTREGUES, "+", "projetos entregues"), (curriculo.total_cursos(), "", "cursos complementares"),
            (curriculo.total_horas(), "h", "de formação complementar"), (len(curriculo.PREMIOS), "", "prêmios e destaques"),
        ]))
        gravar("selos/seguidores.json", selo(numero(s["seguidores"]), legivel(tema.c2), "github", "seguidores"))
        for chave, rotulo, cor in METRICAS:
            mensagem = f"{s[chave]} {'dia' if s[chave] == 1 else 'dias'}" if chave in EM_DIAS else numero(s[chave])
            gravar(f"selos/{chave}.json", selo(mensagem, legivel(getattr(tema, cor)), rotulo=rotulo))
        for r in dados["repos"]:
            gravar(f"selos/repo-{r['nome']}.json",
                   selo(ha_quanto(date.fromisoformat(r["atualizado"]), hoje), legivel(tema.c1)))
        blocos["projetos"] = bloco_projetos(dados["repos"])
        if "todos" in dados:
            gravar("radar.svg", radar(tema, dados["todos"], hoje, CORES_LINGUAGENS))
            gravar("relogio.svg", relogio(tema, dados["horas"], dias))
            blocos["todos"] = bloco_todos(dados["todos"])
            blocos["sites"] = bloco_sites(dados["sites"])
    if args.readme:
        atualizar_readme(blocos)

    escrever_saida(tema)
    return 0


if __name__ == "__main__":
    sys.exit(main())

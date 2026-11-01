"""Gera as imagens dinâmicas do perfil (banner, cards, cabeçalhos e rodapé).

O README.md é fixo e aponta para essas imagens na branch "output". O workflow
publica a pasta de saída lá, então nada é commitado na main.

Uso:
    python .github/scripts/perfil.py                   # tema do dia
    python .github/scripts/perfil.py --tema natal      # força um tema
    python .github/scripts/perfil.py --data 2026-12-25 # simula uma data
    python .github/scripts/perfil.py --offline         # não acessa a API
    python .github/scripts/perfil.py --listar          # calendário de temas
    python .github/scripts/perfil.py --saida dist      # pasta de saída (padrão)

Usa apenas a biblioteca padrão. GITHUB_TOKEN é opcional localmente, mas no
Actions evita o limite de requisições e libera o calendário via GraphQL.
"""

import argparse
import base64
import io
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
from banner import banner
from temas import PADRAO, TEMAS, Tema, legivel, misturar, tema_do_dia

USUARIO = "GuiiBM"
RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "dist"
BRASILIA = timezone(timedelta(hours=-3))

# Textos do banner do topo.
NOME = "Guilherme Batistela"
COMANDO = "root@guiibm:~$ whoami"
CHIPS = ["ADS @ Fatec", "Pesquisador PIBICT", "Red Team", "Linux Mint"]
# Foto do banner: se existir, este arquivo substitui a foto de perfil do GitHub.
FOTO_LOCAL = Path(__file__).with_name("foto.jpg")

# Cabeçalhos das seções (assets/secoes/01.svg, 02.svg...): título e comando.
SECOES = [
    ("Sobre Mim", "whoami --verbose"),
    ("Trajetória", "cat ~/trajetoria.log"),
    ("Formação & Prêmios", "ls ~/certificados ~/premios"),
    ("Arsenal Tecnológico", "ls -la ~/arsenal"),
    ("Projetos", "git log --oneline --recent"),
    ("Métricas de Código", "gh stats --last-12-months"),
    ("Atividade em Tempo Real", "tail -f ~/contributions.log"),
    ("Calendário 3D de Contribuições", "render --isometric --year"),
    ("Conquistas no GitHub", "cat ~/trophies.txt"),
]

# Quantidade de cards de repositório (o README referencia repos/1.svg a 6.svg).
TOTAL_REPOS = 6
# Repositórios que não devem aparecer em "Repositórios recentes".
REPOS_IGNORADOS = {USUARIO}
# Descrições usadas quando o repositório não tem uma no GitHub. Sem as
# duas, o card usa o primeiro parágrafo do README do repositório.
DESCRICOES: dict[str, str] = {
    # "tcc": "Trabalho de conclusão de curso em PHP.",
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

FONTE = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace"
FUNDO, TEXTO, APAGADO = "0d1117", "e2e8f0", "8b949e"


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


def comprimir_foto(bruto: bytes, lado: int = 280) -> bytes | None:
    """Reduz a foto para JPEG com o Pillow, se ele estiver instalado."""
    try:
        from PIL import Image
    except ImportError:
        return None
    imagem = Image.open(io.BytesIO(bruto)).convert("RGB")
    imagem.thumbnail((lado, lado))
    saida = io.BytesIO()
    imagem.save(saida, "JPEG", quality=85, optimize=True)
    return saida.getvalue()


def data_uri_foto(bruto: bytes) -> str:
    jpeg = comprimir_foto(bruto)
    if jpeg:
        return f"data:image/jpeg;base64,{base64.b64encode(jpeg).decode()}"
    tipo = "image/png" if bruto[:4] == b"\x89PNG" else "image/jpeg"
    return f"data:{tipo};base64,{base64.b64encode(bruto).decode()}"


def avatar() -> str:
    """Foto de perfil do GitHub como data URI, para embutir no banner."""
    tamanho = 280
    try:
        import PIL  # noqa: F401
    except ImportError:
        tamanho = 140  # sem Pillow, baixa menor para o banner não ficar pesado
    return data_uri_foto(requisitar(f"https://avatars.githubusercontent.com/{USUARIO}?s={tamanho}&v=4"))


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
    recentes = [r for r in proprios if r["name"] not in REPOS_IGNORADOS and not r["archived"]][:TOTAL_REPOS]
    for r in recentes:
        r["resumo"] = r["description"] or DESCRICOES.get(r["name"]) or resumo_readme(r)
    return {
        "repos": [{"nome": r["name"], "url": r["html_url"], "resumo": r["resumo"],
                   "linguagem": r["language"], "estrelas": r["stargazers_count"],
                   "atualizado": r["pushed_at"][:10]} for r in recentes],
        "linguagens": linguagens,
        "avatar": avatar(),
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
        },
    }


# --------------------------------------------------------------------------
# Cards SVG
# --------------------------------------------------------------------------

def esc(texto) -> str:
    return html.escape(str(texto), quote=True)


def numero(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def estilo_base(t: Tema) -> str:
    return f"""<style>
    text {{ font-family: {FONTE}; }}
    .titulo {{ font-size: 18px; font-weight: 600; fill: #{t.acento}; }}
    .rotulo {{ font-size: 13.5px; fill: #{TEXTO}; }}
    .valor {{ font-size: 13.5px; font-weight: 700; fill: #ffffff; }}
    .apagado {{ font-size: 11.5px; fill: #{APAGADO}; }}
    .surge {{ animation: surgir .6s ease-out both; }}
    @keyframes surgir {{ from {{ opacity: 0; transform: translateX(-8px); }} to {{ opacity: 1; transform: none; }} }}
    @media (prefers-reduced-motion: reduce) {{ .surge, .anima {{ animation: none !important; }} }}
  </style>"""


def moldura(t: Tema, largura: int, altura: int, titulo: str, corpo: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="{esc(titulo)}">
  <title>{esc(titulo)}</title>
  {estilo_base(t)}
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#{t.c1}"/><stop offset="100%" stop-color="#{t.c2}"/>
    </linearGradient>
    <clipPath id="card"><rect x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="10"/></clipPath>
  </defs>
  <rect x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="10" fill="#{FUNDO}" stroke="#{t.c1}" stroke-opacity="0.6"/>
  <rect x="0" y="0" width="{largura}" height="4" fill="url(#grad)" clip-path="url(#card)"/>
  <text x="25" y="38" class="titulo">{esc(titulo)}</text>
{corpo}
</svg>
"""


def card_stats(t: Tema, s: dict) -> str:
    itens = [
        ("Contribuições (12 meses)", s["contribuicoes"]),
        ("Commits (12 meses)", s["commits"]),
        ("Pull requests (12 meses)", s["prs"]),
        ("Issues (12 meses)", s["issues"]),
        ("Repositórios públicos", s["repos"]),
        ("Estrelas recebidas", s["estrelas"]),
    ]
    linhas = []
    for i, (rotulo, valor) in enumerate(itens):
        y = 72 + i * 23
        cor = legivel(t.c1 if i % 2 == 0 else t.c2)
        linhas.append(
            f'  <g class="surge" style="animation-delay:{150 + i * 90}ms">'
            f'<circle cx="31" cy="{y - 4.5}" r="4" fill="#{cor}"/>'
            f'<text x="44" y="{y}" class="rotulo">{esc(rotulo)}</text>'
            f'<text x="300" y="{y}" class="valor" text-anchor="end">{numero(valor)}</text></g>'
        )

    raio = 44
    volta = 2 * 3.14159 * raio
    fracao = min(s["seq_atual"] / s["seq_maior"], 1) if s["seq_maior"] else 0
    cx, cy = 400, 118
    anel = f"""  <style>
    .anel {{ stroke-dasharray: {volta:.1f}; stroke-dashoffset: {volta * (1 - fracao):.1f}; animation: encher 1.2s ease-out .3s both; }}
    @keyframes encher {{ from {{ stroke-dashoffset: {volta:.1f}; }} }}
    @media (prefers-reduced-motion: reduce) {{ .anel {{ animation: none; }} }}
  </style>
  <circle cx="{cx}" cy="{cy}" r="{raio}" fill="none" stroke="#{t.c1}" stroke-opacity="0.18" stroke-width="7"/>
  <circle cx="{cx}" cy="{cy}" r="{raio}" fill="none" stroke="url(#grad)" stroke-width="7" stroke-linecap="round" class="anel" transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy + 2}" text-anchor="middle" style="font-size:28px;font-weight:700;fill:#{t.acento}">{s["seq_atual"]}</text>
  <text x="{cx}" y="{cy + 20}" text-anchor="middle" class="apagado">dias seguidos</text>
  <text x="{cx}" y="{cy + 68}" text-anchor="middle" class="apagado">recorde: {s["seq_maior"]} dias</text>"""
    return moldura(t, 495, 210, f"Estatísticas de {USUARIO}", "\n".join(linhas) + "\n" + anel)


def card_linguagens(t: Tema, linguagens: dict[str, int]) -> str:
    total = sum(linguagens.values()) or 1
    top = [(n, b) for n, b in sorted(linguagens.items(), key=lambda x: -x[1]) if b / total >= 0.001][:6]
    paleta = [legivel(t.c1), legivel(t.c2), t.acento]
    cores = [CORES_LINGUAGENS.get(n, paleta[i % 3]) for i, (n, _) in enumerate(top)]

    largura, x = 300, 25.0
    barras = []
    for (nome, b), cor in zip(top, cores):
        w = largura * b / total
        barras.append(f'<rect x="{x:.2f}" y="56" width="{max(w, 0.5):.2f}" height="10" fill="#{cor}"/>')
        x += w
    barra = (f'  <clipPath id="barra"><rect x="25" y="56" width="{largura}" height="10" rx="5"/></clipPath>\n'
             f'  <g clip-path="url(#barra)" class="surge">{"".join(barras)}</g>')

    legenda = []
    for i, ((nome, b), cor) in enumerate(zip(top, cores)):
        coluna, linha = divmod(i, 3)
        lx, ly = 25 + coluna * 160, 104 + linha * 32
        legenda.append(
            f'  <g class="surge" style="animation-delay:{200 + i * 70}ms">'
            f'<circle cx="{lx + 5}" cy="{ly - 4.5}" r="5" fill="#{cor}"/>'
            f'<text x="{lx + 16}" y="{ly}" class="rotulo">{esc(nome)}</text>'
            f'<text x="{lx + 140}" y="{ly}" class="apagado" text-anchor="end">{100 * b / total:.1f}%</text></g>'
        )
    return moldura(t, 350, 210, "Linguagens mais usadas", barra + "\n" + "\n".join(legenda))


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
        return "atualizado hoje"
    if dias == 1:
        return "atualizado ontem"
    if dias < 45:
        return f"atualizado há {dias} dias"
    meses = round(dias / 30)
    return f"atualizado há {meses} meses" if meses < 12 else f"atualizado há {dias // 365} ano(s)"


def card_repo(t: Tema, r: dict, hoje: date) -> str:
    nome = r["nome"] if len(r["nome"]) <= 40 else r["nome"][:39] + "…"
    resumo = r["resumo"] or "Sem descrição por enquanto. Abra o repositório para ver o código."
    linhas = quebrar(resumo, 62, 2)
    texto = "".join(f'<text x="25" y="{70 + i * 20}" class="rotulo" style="fill:#{APAGADO if not r["resumo"] else TEXTO}">'
                    f"{esc(l)}</text>" for i, l in enumerate(linhas))
    cor = CORES_LINGUAGENS.get(r["linguagem"] or "", legivel(t.c1))
    rodape = []
    x = 25
    if r["linguagem"]:
        rodape.append(f'<circle cx="{x + 6}" cy="125.5" r="6" fill="#{cor}"/>'
                      f'<text x="{x + 18}" y="130" class="apagado" style="font-size:12.5px">{esc(r["linguagem"])}</text>')
        x += 32 + 7 * len(r["linguagem"])
    if r["estrelas"]:
        rodape.append(f'<text x="{x}" y="130" class="apagado" style="font-size:12.5px">★ {r["estrelas"]}</text>')
    rodape.append(f'<text x="435" y="130" class="apagado" text-anchor="end" style="font-size:12.5px">'
                  f'{ha_quanto(date.fromisoformat(r["atualizado"]), hoje)}</text>')
    icone = (f'<path transform="translate(435 22)" fill="#{legivel(t.acento)}" opacity=".45" '
             'd="M-14 0h10a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2h-11zM2 0h10v13H1a2 2 0 0 0-2 2V3a3 3 0 0 1 3-3z"/>')
    corpo = f'  <g class="surge">{texto}</g>\n  {"".join(rodape)}\n  {icone}'
    return moldura(t, 460, 150, nome, corpo)


def card_secao(t: Tema, numero: int, titulo: str, comando: str) -> str:
    largura, altura, total = 1000, 72, len(SECOES)
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    pontos = "".join(
        f'<circle cx="{largura - 30 - (total - 1 - i) * 14}" cy="47" r="4" '
        + (f'fill="#{acento}"/>' if i == numero - 1 else f'fill="none" stroke="#{APAGADO}" stroke-opacity=".6"/>')
        for i in range(total))
    rotulo = f"[0x{numero:02X}] {titulo}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="{esc(rotulo)}">
  <title>{esc(rotulo)}</title>
  <style>
    .brilho {{ animation: varrer 5s ease-in-out infinite; }}
    .cursor {{ animation: piscar 1s steps(1) infinite; }}
    @keyframes varrer {{ from {{ transform: translateX(-300px); }} to {{ transform: translateX({largura + 300}px); }} }}
    @keyframes piscar {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .brilho, .cursor {{ animation: none; }} .brilho {{ display: none; }} }}
  </style>
  <defs>
    <linearGradient id="lateral" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#{c1}"/><stop offset="100%" stop-color="#{c2}"/></linearGradient>
    <linearGradient id="fundo" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#{c1}" stop-opacity=".16"/><stop offset="60%" stop-color="#{FUNDO}" stop-opacity="0"/></linearGradient>
    <linearGradient id="luz" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#fff" stop-opacity="0"/><stop offset="50%" stop-color="#fff" stop-opacity=".06"/><stop offset="100%" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="barra"><rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#barra)">
    <rect width="{largura}" height="{altura}" fill="#{FUNDO}"/>
    <rect width="{largura}" height="{altura}" fill="url(#fundo)"/>
    <rect width="5" height="{altura}" fill="url(#lateral)"/>
    <rect x="0" width="260" height="{altura}" fill="url(#luz)" class="brilho"/>
  </g>
  <rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="12" fill="none" stroke="#{c1}" stroke-opacity=".5"/>

  <rect x="26" y="19" width="78" height="34" rx="8" fill="#{c1}" fill-opacity=".16" stroke="#{c1}" stroke-opacity=".75"/>
  <text x="65" y="41" text-anchor="middle" style="font:700 15px {MONO};fill:#{acento}">0x{numero:02X}</text>
  <text x="124" y="34" style="font:700 22px {FONTE};fill:#ffffff">{esc(titulo)}</text>
  <text x="124" y="56" style="font:500 12.5px {MONO};fill:#{APAGADO}"><tspan fill="#{c2}">$</tspan> {esc(comando)}<tspan class="cursor" fill="#{acento}"> ▌</tspan></text>

  <text x="{largura - 26}" y="30" text-anchor="end" style="font:600 12px {MONO};fill:#{APAGADO};letter-spacing:1px">{numero:02d} / {total:02d}</text>
  {pontos}
</svg>
"""


def card_trajetoria(t: Tema) -> str:
    itens, passo = curriculo.TRAJETORIA, 92
    altura = 70 + passo * len(itens) - 4
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    corpo = [f'  <line x1="150" y1="78" x2="150" y2="{70 + passo * (len(itens) - 1) + 8}" stroke="url(#grad)" stroke-width="2" opacity=".6"/>']
    for i, (periodo, cargo, instituicao, descricao) in enumerate(itens):
        y = 70 + i * passo
        cor = c1 if i % 2 == 0 else c2
        linhas = "".join(f'<text x="175" y="{y + 54 + k * 17}" class="apagado" style="font-size:12.5px">{esc(l)}</text>'
                         for k, l in enumerate(quebrar(descricao, 118, 2)))
        corpo.append(
            f'  <g class="surge" style="animation-delay:{150 + i * 120}ms">'
            f'<text x="128" y="{y + 13}" text-anchor="end" style="font:600 12px {MONO};fill:#{acento}">{esc(periodo)}</text>'
            f'<circle cx="150" cy="{y + 8}" r="9" fill="#{cor}" fill-opacity=".2"/><circle cx="150" cy="{y + 8}" r="5" fill="#{cor}"/>'
            f'<text x="175" y="{y + 14}" style="font:700 16px {FONTE};fill:#ffffff">{esc(cargo)}</text>'
            f'<text x="175" y="{y + 33}" style="font:600 13px {FONTE};fill:#{cor}">{esc(instituicao)}</text>'
            f"{linhas}</g>")
    return moldura(t, 1000, altura, "Experiência & Pesquisa", "\n".join(corpo))


def card_formacao(t: Tema) -> str:
    c2, acento = legivel(t.c2), legivel(t.acento)
    subtitulo = lambda x, y, texto: (f'<text x="{x}" y="{y}" style="font:700 11.5px {MONO};fill:#{APAGADO};'
                                     f'letter-spacing:2px">{esc(texto)}</text>')
    corpo = [subtitulo(25, 74, "FORMAÇÃO"), subtitulo(520, 74, "CERTIFICAÇÕES")]
    y = 102
    for periodo, curso, instituicao in curriculo.FORMACAO:
        corpo.append(f'<g class="surge"><text x="25" y="{y}" style="font:700 15px {FONTE};fill:#ffffff">{esc(curso)}</text>'
                     f'<text x="25" y="{y + 20}" class="apagado" style="font-size:12.5px">'
                     f'<tspan fill="#{acento}">{esc(periodo)}</tspan>  ·  {esc(instituicao)}</text></g>')
        y += 54
    corpo.append(subtitulo(25, y + 8, "IDIOMAS"))
    corpo.append(f'<text x="25" y="{y + 36}" class="rotulo">Português <tspan class="apagado">nativo</tspan>'
                 f'   ·   Inglês <tspan class="apagado">intermediário (B1)</tspan></text>')
    for i, (ano, nome, instituicao) in enumerate(curriculo.CERTIFICACOES):
        cy = 102 + i * 44
        corpo.append(f'<g class="surge" style="animation-delay:{200 + i * 80}ms">'
                     f'<rect x="520" y="{cy - 12}" width="3" height="32" rx="1.5" fill="#{c2}"/>'
                     f'<text x="534" y="{cy}" style="font:600 14px {FONTE};fill:#ffffff">{esc(nome)}</text>'
                     f'<text x="534" y="{cy + 18}" class="apagado" style="font-size:12px">{esc(instituicao)} · {ano}</text></g>')
    altura = max(102 + 44 * len(curriculo.CERTIFICACOES), y + 56)
    corpo.insert(0, f'<line x1="495" y1="62" x2="495" y2="{altura - 24}" stroke="#{APAGADO}" stroke-opacity=".2"/>')
    return moldura(t, 1000, altura, "Formação & Certificações", "\n  ".join(corpo))


def card_premios(t: Tema) -> str:
    cores = {"ouro": "f5c542", "prata": "c0c7d1", "bronze": "cd7f32", "marca": legivel(t.acento)}
    itens = []
    for i, (ano, titulo, detalhe, nivel) in enumerate(curriculo.PREMIOS):
        linha, coluna = divmod(i, 2)
        x, y = 25 + coluna * 480, 60 + linha * 74
        cor = cores[nivel]
        icone = (f'<path d="M{x + 22} {y + 40} l-7 14 7-4 7 4z M{x + 34} {y + 40} l-7 14 7-4 7 4z" fill="#{cor}" opacity=".7"/>'
                 f'<circle cx="{x + 28}" cy="{y + 31}" r="14" fill="#{cor}"/>'
                 f'<circle cx="{x + 28}" cy="{y + 31}" r="9" fill="none" stroke="#{FUNDO}" stroke-opacity=".45" stroke-width="2"/>')
        itens.append(
            f'  <g class="surge" style="animation-delay:{150 + i * 70}ms">'
            f'<rect x="{x}" y="{y}" width="470" height="62" rx="10" fill="#{cor}" fill-opacity=".07" stroke="#{cor}" stroke-opacity=".35"/>'
            f"{icone}"
            f'<text x="{x + 56}" y="{y + 27}" style="font:700 14.5px {FONTE};fill:#ffffff">{esc(titulo)}</text>'
            f'<text x="{x + 56}" y="{y + 46}" class="apagado" style="font-size:12px">{esc(detalhe)}</text>'
            f'<text x="{x + 456}" y="{y + 27}" text-anchor="end" style="font:600 11.5px {MONO};fill:#{cor}">{esc(ano)}</text></g>')
    altura = 60 + 74 * ((len(curriculo.PREMIOS) + 1) // 2) + 12
    return moldura(t, 1000, altura, "Prêmios & Destaques", "\n".join(itens))


def card_repo_vazio(t: Tema) -> str:
    corpo = f'  <text x="25" y="70" class="rotulo" style="fill:#{APAGADO}">Espaço reservado para o próximo projeto.</text>'
    return moldura(t, 460, 150, "Em breve", corpo)


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
    (saida / "repos").mkdir(parents=True, exist_ok=True)
    (saida / "secoes").mkdir(exist_ok=True)
    gravar = lambda nome, conteudo: (saida / nome).write_text(conteudo, encoding="utf-8")

    ano_novo = hoje.year + 1 if hoje.month == 12 else hoje.year
    subtitulo = tema.descricao.format(ano_novo=ano_novo).replace(" | ", " · ")
    gravar("rodape.svg", card_rodape(tema, hoje, agora))
    for i, (titulo, comando) in enumerate(SECOES, 1):
        gravar(f"secoes/{i:02d}.svg", card_secao(tema, i, titulo, comando))
    gravar("trajetoria.svg", card_trajetoria(tema))
    gravar("formacao.svg", card_formacao(tema))
    gravar("premios.svg", card_premios(tema))

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

    if FOTO_LOCAL.exists():
        foto = data_uri_foto(FOTO_LOCAL.read_bytes())
    else:
        foto = dados.get("avatar") if dados else None
    gravar("banner.svg", banner(tema, hoje, NOME, subtitulo, COMANDO, CHIPS, foto))

    repos = dados["repos"] if dados else []
    for i in range(TOTAL_REPOS):
        gravar(f"repos/{i + 1}.svg", card_repo(tema, repos[i], hoje) if i < len(repos) else card_repo_vazio(tema))
    if dados:
        dias = {date.fromisoformat(d): n for d, n in dados["dias"].items()}
        gravar("stats.svg", card_stats(tema, dados["stats"]))
        gravar("linguagens.svg", card_linguagens(tema, dados["linguagens"]))
        gravar("atividade.svg", card_atividade(tema, dias, hoje))

    escrever_saida(tema)
    return 0


if __name__ == "__main__":
    sys.exit(main())

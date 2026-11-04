"""Animações próprias do perfil, todas alimentadas por dados reais.

Odômetro, terminal, radar de repositórios, linha do tempo e o emblema 3D (STL
que o GitHub deixa girar com o mouse). Tudo que tem texto anima uma vez e fica
parado, para ser lido com calma; só a varredura do radar segue em movimento.
As animações são CSS, para respeitar prefers-reduced-motion.
"""

import math
from datetime import date

import curriculo
from estilo import APAGADO, FUNDO, MONO, TEXTO, esc, moldura, numero
from temas import Tema, legivel

CORES_MEDALHA = {"ouro": "f5c542", "prata": "c0c7d1", "bronze": "cd7f32"}


def odometro(t: Tema, itens: list[tuple[int, str, str]]) -> str:
    """Números que rolam até o valor real: (valor, sufixo, rótulo)."""
    largura, altura, passo = 1000, 164, 44
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    coluna = (largura - 40) / len(itens)
    corpo = ["""  <style>
    .rolo { animation: rolar 2s cubic-bezier(.2,.8,.2,1) backwards; }
    @keyframes rolar { from { transform: translateY(0); } }
    @media (prefers-reduced-motion: reduce) { .rolo { animation: none; } }
  </style>"""]
    for i, (valor, sufixo, rotulo) in enumerate(itens):
        meio = 20 + coluna * (i + .5)
        cor = c1 if i % 2 == 0 else c2
        digitos = f"{valor}"
        largura_digito = 24
        x0 = meio - (len(digitos) + len(sufixo)) * largura_digito / 2
        for j, d in enumerate(digitos):
            x = x0 + j * largura_digito
            corpo.append(f'  <clipPath id="j{i}-{j}"><rect x="{x:.1f}" y="60" width="{largura_digito}" height="{passo}"/></clipPath>')
            fita = "".join(f'<text x="{x + largura_digito / 2:.1f}" y="{94 + n * passo}" text-anchor="middle" '
                           f'style="font:700 36px {MONO};fill:#{acento}">{n}</text>' for n in range(10))
            corpo.append(f'  <g clip-path="url(#j{i}-{j})"><g class="rolo" style="transform:translateY({-int(d) * passo}px);'
                         f'animation-delay:{i * 120 + j * 90}ms">{fita}</g></g>')
        if sufixo:
            corpo.append(f'  <text x="{x0 + len(digitos) * largura_digito + 12:.1f}" y="94" text-anchor="middle" '
                         f'style="font:700 36px {MONO};fill:#{cor}">{esc(sufixo)}</text>')
        corpo.append(f'  <rect x="{meio - 22:.1f}" y="112" width="44" height="3" rx="1.5" fill="#{cor}"/>')
        corpo.append(f'  <text x="{meio:.1f}" y="136" text-anchor="middle" class="rotulo" style="font-size:12.5px">{esc(rotulo)}</text>')
    return moldura(t, largura, altura, "Em números", "\n".join(corpo))


def terminal(t: Tema, dados: dict, hoje: date) -> str:
    """Janela de terminal que digita comandos e mostra as respostas, em laço."""
    s = dados["stats"]
    portas = {"Python": 8000, "PHP": 80, "HTML": 443, "JavaScript": 3000, "CSS": 8080, "C": 31337, "Shell": 22}
    total = sum(dados["linguagens"].values()) or 1
    top = sorted(dados["linguagens"].items(), key=lambda x: -x[1])[:5]
    ultimo = dados["repos"][0] if dados["repos"] else None

    linhas: list[tuple[str, list[tuple[int, str, str]]]] = [
        ("cmd", [(0, "whoami", "")]),
        ("out", [(0, "Guilherme Batistela Machado · ADS @ Fatec · bolsista PIBICT · Red Team", TEXTO)]),
        ("cmd", [(0, "nmap -sV github.com/GuiiBM", "")]),
        ("out", [(0, f"{s['repos']} repositórios públicos · {numero(s['contribuicoes'])} contribuições em 12 meses", APAGADO)]),
        ("out", [(0, "PORT", APAGADO), (11, "STATE", APAGADO), (19, "SERVICE", APAGADO), (34, "VERSION", APAGADO)]),
    ]
    for i, (nome, bytes_) in enumerate(top):
        linhas.append(("out", [(0, f"{portas.get(nome, 9000 + i)}/tcp", TEXTO), (11, "open", "3fb950"), (19, nome.lower(), TEXTO),
                               (34, f"{100 * bytes_ / total:.1f}% do código", APAGADO)]))
    if ultimo:
        linhas += [("cmd", [(0, "git log -1 --format=%s", "")]),
                   ("out", [(0, f"último push: {ultimo['nome']} em {ultimo['atualizado']}", TEXTO)])]
    linhas += [("cmd", [(0, "uptime", "")]),
               ("out", [(0, f"sequência atual: {s['seq_atual']} dias · recorde: {s['seq_maior']} dias · {s['prs']} PRs", TEXTO)]),
               ("fim", [])]

    largura, topo, altura_linha, tam = 1000, 62, 23, 14
    altura = topo + altura_linha * len(linhas) + 12
    char = tam * .6
    prompt = "root@guiibm:~$ "
    acento, c2 = legivel(t.acento), legivel(t.c2)

    # Cada linha surge no seu instante e fica: comandos levam o tempo de digitação.
    estilos, corpo, agora = [".linha { animation: aparece .01s linear backwards; }",
                             "@keyframes aparece { from, to { opacity: 0; } }"], [], .5
    for i, (tipo, partes) in enumerate(linhas):
        y = topo + i * altura_linha
        grupo = []
        if tipo in ("cmd", "fim"):
            grupo.append(f'<text x="25" y="{y}" style="font:600 {tam}px {MONO};fill:#{c2}" xml:space="preserve">{esc(prompt)}</text>')
        x0 = 25 + len(prompt) * char
        if tipo == "cmd":
            texto = partes[0][1]
            duracao = len(texto) * .05
            deslocamento = len(texto) * char + 4
            grupo.append(f'<text x="{x0:.1f}" y="{y}" style="font:600 {tam}px {MONO};fill:#{acento}">{esc(texto)}</text>')
            estilos.append(f"@keyframes d{i} {{ to {{ transform: translateX({deslocamento:.1f}px); }} }}"
                           f" .d{i} {{ animation: d{i} {duracao:.2f}s steps({len(texto)}) {agora:.2f}s forwards; }}")
            grupo.append(f'<rect class="cobre d{i}" x="{x0 - 1:.1f}" y="{y - tam}" width="{deslocamento + 2:.1f}" height="{tam + 6}" fill="#{FUNDO}"/>')
        elif tipo == "out":
            duracao = .08
            for coluna, texto, cor in partes:
                grupo.append(f'<text x="{25 + coluna * char:.1f}" y="{y}" style="font:500 {tam}px {MONO};fill:#{cor}">{esc(texto)}</text>')
        else:
            duracao = 0
            grupo.append(f'<rect class="pisca" x="{x0:.1f}" y="{y - tam + 1}" width="{char:.1f}" height="{tam + 2}" fill="#{acento}"/>')
        corpo.append(f'  <g class="linha" style="animation-delay:{agora:.2f}s">{"".join(grupo)}</g>')
        agora += duracao + (.3 if tipo == "cmd" else .06)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Terminal com um resumo do perfil">
  <title>Terminal com um resumo do perfil</title>
  <style>
    {chr(10).join("    " + e for e in estilos).strip()}
    .pisca {{ animation: pisca 1s steps(1) infinite; }}
    @keyframes pisca {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .linha, .cobre, .pisca {{ animation: none !important; }} .cobre {{ display: none; }} }}
  </style>
  <defs><clipPath id="janela"><rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="10"/></clipPath></defs>
  <g clip-path="url(#janela)">
    <rect width="{largura}" height="{altura}" fill="#{FUNDO}"/>
    <rect width="{largura}" height="34" fill="#161b22"/>
    <circle cx="22" cy="17" r="6" fill="#ff5f56"/><circle cx="42" cy="17" r="6" fill="#ffbd2e"/><circle cx="62" cy="17" r="6" fill="#27c93f"/>
    <text x="{largura / 2}" y="22" text-anchor="middle" style="font:600 13px {MONO};fill:#{APAGADO}">root@guiibm: ~/profile</text>
{chr(10).join(corpo)}
  </g>
  <rect x=".5" y=".5" width="{largura - 1}" height="{altura - 1}" rx="10" fill="none" stroke="#{legivel(t.c1)}" stroke-opacity=".55"/>
</svg>
"""


def radar(t: Tema, repos: list[dict], hoje: date, cores: dict[str, str]) -> str:
    """Radar de repositórios: quanto mais perto do centro, mais recente o push."""
    largura, altura, cx, cy, raio = 1000, 540, 285, 290, 225
    ciclo = 8
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    distancia = lambda d: raio * (.14 + .86 * min(math.log1p(d) / math.log1p(800), 1))
    ponto = lambda r, a: (cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a)))

    aneis, rotulos = [], []
    for dias_, rotulo in ((7, "7 dias"), (30, "1 mês"), (180, "6 meses"), (365, "1 ano")):
        r = distancia(dias_)
        aneis.append(f'  <circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="#{c1}" stroke-opacity=".32"/>')
        rotulos.append(f'  <text x="{cx + 5}" y="{cy - r + 13:.1f}" class="apagado" style="font-size:10px">{rotulo}</text>')
    aneis.append(f'  <circle cx="{cx}" cy="{cy}" r="{raio}" fill="#{c1}" fill-opacity=".05" stroke="#{c1}" stroke-opacity=".7" stroke-width="1.5"/>')
    for a in range(0, 360, 30):
        x1, y1 = ponto(raio - 7, a)
        x2, y2 = ponto(raio, a)
        aneis.append(f'  <line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#{c1}" stroke-opacity=".7"/>')
    aneis.append(f'  <line x1="{cx - raio}" y1="{cy}" x2="{cx + raio}" y2="{cy}" stroke="#{c1}" stroke-opacity=".18"/>'
                 f'<line x1="{cx}" y1="{cy - raio}" x2="{cx}" y2="{cy + raio}" stroke="#{c1}" stroke-opacity=".18"/>')

    # Rastro da varredura: fatias atrás da borda, cada vez mais transparentes.
    fatias = []
    for k in range(18):
        x1, y1 = ponto(raio, -k * 4)
        x2, y2 = ponto(raio, -(k + 1) * 4)
        fatias.append(f'<path d="M{cx} {cy}L{x1:.1f} {y1:.1f}A{raio} {raio} 0 0 0 {x2:.1f} {y2:.1f}Z" fill="#{c2}" fill-opacity="{.34 * (1 - k / 18):.3f}"/>')
    x1, y1 = ponto(raio, 0)
    fatias.append(f'<line x1="{cx}" y1="{cy}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#{acento}" stroke-width="2"/>')

    ordenados = sorted(repos, key=lambda r: r["atualizado"], reverse=True)
    ondas, blips, lista = [], [], []
    linha_altura = min(32, 440 / max(len(ordenados), 1))
    for i, r in enumerate(ordenados):
        dias_ = (hoje - date.fromisoformat(r["atualizado"])).days
        angulo = (i * 137.508 + 25) % 360  # ângulo áureo: espalha sem sobrepor
        x, y = ponto(distancia(dias_), angulo)
        cor = cores.get(r["linguagem"] or "", acento)
        atraso = angulo / 360 * ciclo - ciclo
        ondas.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="none" stroke="#{cor}" stroke-width="2" class="onda" style="animation-delay:{atraso:.2f}s"/>')
        blips.append(f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#{cor}"/>'
                     f'<text x="{x:.1f}" y="{y + 3.5:.1f}" text-anchor="middle" style="font:700 10px {MONO};fill:#fff">{i + 1}</text>')
        ly = 82 + i * linha_altura
        nome = r["nome"] if len(r["nome"]) <= 36 else r["nome"][:35] + "…"
        lista.append(f'  <g><circle cx="565" cy="{ly - 4:.1f}" r="9" fill="#{cor}"/>'
                     f'<text x="565" y="{ly - .5:.1f}" text-anchor="middle" style="font:700 9.5px {MONO};fill:#fff">{i + 1}</text>'
                     f'<text x="584" y="{ly:.1f}" class="rotulo">{esc(nome)}</text>'
                     f'<text x="975" y="{ly:.1f}" text-anchor="end" class="apagado">{esc(r["linguagem"] or "")} · {r["atualizado"][8:10]}/{r["atualizado"][5:7]}/{r["atualizado"][2:4]}</text></g>')

    corpo = f"""  <style>
    .varre {{ transform-origin: {cx}px {cy}px; animation: girar {ciclo}s linear infinite; }}
    .onda {{ transform-box: fill-box; transform-origin: center; animation: onda {ciclo}s ease-out infinite; }}
    @keyframes girar {{ to {{ transform: rotate(360deg); }} }}
    @keyframes onda {{ 0% {{ opacity: .9; transform: scale(1); }} 22%, 100% {{ opacity: 0; transform: scale(2.4); }} }}
    @media (prefers-reduced-motion: reduce) {{ .varre, .onda {{ animation: none; }} .onda {{ display: none; }} }}
  </style>
  <text x="975" y="38" text-anchor="end" class="apagado">centro = push mais recente</text>
{chr(10).join(aneis)}
  <g class="varre">{"".join(fatias)}</g>
{chr(10).join(rotulos)}
{chr(10).join(ondas)}
{chr(10).join(blips)}
  <circle cx="{cx}" cy="{cy}" r="3.5" fill="#{acento}"/>
{chr(10).join(lista)}"""
    return moldura(t, largura, altura, "Radar de repositórios", corpo)


def linha_do_tempo(t: Tema, hoje: date) -> str:
    """Barras da carreira que crescem da esquerda para a direita, com os prêmios acima."""
    largura = 1000
    esq, dir_ = 30, 30
    inicio = 2019
    agora = hoje.year + (hoje.timetuple().tm_yday - 1) / 365
    fim_eixo = agora + .35
    escala = (largura - esq - dir_) / (fim_eixo - inicio)
    px = lambda ano: esq + (ano - inicio) * escala
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    cores = {"formacao": c1, "pesquisa": c2, "trabalho": acento}
    nomes = {"formacao": "Formação", "pesquisa": "Pesquisa", "trabalho": "Trabalho e extensão"}

    topo_medalhas, eixo = 66, 126
    y0 = eixo + 28
    passo = 34
    altura = y0 + passo * len(curriculo.LINHA_DO_TEMPO) + 12
    corpo = []
    for ano in range(inicio, hoje.year + 1):
        x = px(ano)
        corpo.append(f'  <line x1="{x:.1f}" y1="{eixo}" x2="{x:.1f}" y2="{altura - 14}" stroke="#{APAGADO}" stroke-opacity=".14"/>'
                     f'<text x="{x + 4:.1f}" y="{eixo - 6}" style="font:600 11.5px {MONO};fill:#{APAGADO}">{ano}</text>')
    corpo.append(f'  <rect x="{esq}" y="{eixo}" width="{largura - esq - dir_}" height="2" fill="#{APAGADO}" fill-opacity=".35"/>')

    # Medalhas por ano, empilhadas quando há mais de uma no mesmo ano.
    por_ano: dict[int, int] = {}
    for ano_txt, titulo, _detalhe, nivel in reversed(curriculo.PREMIOS):
        if nivel not in CORES_MEDALHA:
            continue
        ano = int(ano_txt[:4])
        k = por_ano.get(ano, 0)
        por_ano[ano] = k + 1
        x, y = px(ano + .5) + k * 22, topo_medalhas + 22
        corpo.append(f'  <g class="medalha" style="animation-delay:{(ano - inicio) * 180}ms"><circle cx="{x:.1f}" cy="{y}" r="9" fill="#{CORES_MEDALHA[nivel]}">'
                     f'<title>{esc(titulo)} ({ano})</title></circle><circle cx="{x:.1f}" cy="{y}" r="5" fill="none" stroke="#{FUNDO}" stroke-opacity=".45" stroke-width="1.5"/></g>')

    for i, (rotulo, ini, fim, faixa) in enumerate(curriculo.LINHA_DO_TEMPO):
        y = y0 + i * passo
        x1, x2 = px(ini), px(fim if fim else agora)
        cor = cores[faixa]
        atual = fim is None
        corpo.append(f'  <rect x="{x1:.1f}" y="{y}" width="{x2 - x1:.1f}" height="20" rx="5" fill="#{cor}" fill-opacity="{.95 if atual else .75}" '
                     f'class="barra" style="animation-delay:{200 + i * 140}ms"/>')
        tamanho = len(rotulo) * 6.4
        tx, ancora = (x2 + 8, "start") if x2 + 8 + tamanho < largura - dir_ else (x1 - 8, "end")
        corpo.append(f'  <text x="{tx:.1f}" y="{y + 14.5}" text-anchor="{ancora}" class="rotulo surge" style="font-size:12.5px;animation-delay:{700 + i * 140}ms">{esc(rotulo)}</text>')

    xh = px(agora)
    corpo.append(f'  <line x1="{xh:.1f}" y1="{eixo - 4}" x2="{xh:.1f}" y2="{altura - 14}" stroke="#{acento}" stroke-width="1.5" stroke-dasharray="4 4"/>'
                 f'<text x="{xh:.1f}" y="{eixo - 8}" text-anchor="middle" style="font:700 11px {MONO};fill:#{acento}">hoje</text>')

    legenda, lx = [], largura - 25
    for faixa in ("trabalho", "pesquisa", "formacao"):
        nome = nomes[faixa]
        lx -= len(nome) * 6.6
        legenda.append(f'  <text x="{lx:.1f}" y="38" class="apagado">{esc(nome)}</text><rect x="{lx - 16:.1f}" y="28" width="11" height="11" rx="3" fill="#{cores[faixa]}"/>')
        lx -= 30

    estilos = """  <style>
    .barra { transform-box: fill-box; transform-origin: left center; animation: crescer 1.1s cubic-bezier(.2,.8,.2,1) backwards; }
    .medalha { animation: surgir .6s ease-out backwards; }
    @keyframes crescer { from { transform: scaleX(0); } }
    @media (prefers-reduced-motion: reduce) { .barra, .medalha { animation: none; } }
  </style>"""
    return moldura(t, largura, altura, "Linha do tempo", estilos + "\n" + "\n".join(legenda + corpo))


# --------------------------------------------------------------------------
# Emblema 3D: o GitHub transforma um bloco ```stl em um modelo que gira no mouse
# --------------------------------------------------------------------------

def _facet(a, b, c) -> str:
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    tamanho = math.sqrt(sum(x * x for x in n)) or 1
    fmt = lambda p: " ".join(f"{x:.3g}" if abs(x) < 100 else f"{x:.0f}" for x in p)
    return (f"facet normal {fmt([x / tamanho for x in n])}\nouter loop\n"
            f"vertex {fmt(a)}\nvertex {fmt(b)}\nvertex {fmt(c)}\nendloop\nendfacet\n")


def _prisma(pontos: list[tuple[float, float]], z0: float, z1: float) -> str:
    """Prisma de base convexa, com os pontos em sentido anti-horário."""
    saida = []
    p0 = pontos[0]
    for a, b in zip(pontos[1:], pontos[2:]):
        saida.append(_facet((*p0, z1), (*a, z1), (*b, z1)))
        saida.append(_facet((*p0, z0), (*b, z0), (*a, z0)))
    for a, b in zip(pontos, pontos[1:] + pontos[:1]):
        saida.append(_facet((*a, z0), (*b, z0), (*b, z1)))
        saida.append(_facet((*a, z0), (*b, z1), (*a, z1)))
    return "".join(saida)


def emblema_stl() -> str:
    """Hexágono com GBM em relevo, o mesmo emblema do banner."""
    raio = 52
    hexagono = [(raio * math.cos(math.radians(90 + k * 60)), raio * math.sin(math.radians(90 + k * 60))) for k in range(6)]
    partes = [_prisma(hexagono, 0, 3)]
    for k in range(6):  # anel em relevo na borda
        a, b = hexagono[k], hexagono[(k + 1) % 6]
        interno = [(x * .86, y * .86) for x, y in (a, b)]
        partes.append(_prisma([a, b, interno[1], interno[0]], 3, 7))

    relevo = 16  # letras bem altas: a luz do visualizador cria o contraste nas laterais

    def caixa(x, y, l, a):
        return _prisma([(x, y), (x + l, y), (x + l, y + a), (x, y + a)], 3, relevo)

    h, e = 28, 5  # altura das letras e espessura do traço
    base = -h / 2
    topo = base + h
    meio = base + h / 2
    l = 21
    xg, xb, xm = -36, -11, 14
    partes += [  # G
        caixa(xg, base, e, h), caixa(xg, topo - e, l, e), caixa(xg, base, l, e),
        caixa(xg + l - e, base, e, h / 2), caixa(xg + l / 2, meio - e / 2, l / 2, e),
    ]
    partes += [  # B
        caixa(xb, base, e, h), caixa(xb, base, l - 3, e), caixa(xb, topo - e, l - 3, e),
        caixa(xb, meio - e / 2, l - 3, e), caixa(xb + l - e, base + 2, e, h / 2 - 3), caixa(xb + l - e, meio + 1, e, h / 2 - 3),
    ]
    partes += [  # M
        caixa(xm, base, e, h), caixa(xm + l - e, base, e, h),
        _prisma([(xm, topo), (xm + l / 2 - e / 2, base + 7), (xm + l / 2 + e / 2, base + 7), (xm + e, topo)], 3, relevo),
        _prisma([(xm + l - e, topo), (xm + l / 2 - e / 2, base + 7), (xm + l / 2 + e / 2, base + 7), (xm + l, topo)], 3, relevo),
    ]
    return "solid gbm\n" + "".join(partes) + "endsolid gbm"

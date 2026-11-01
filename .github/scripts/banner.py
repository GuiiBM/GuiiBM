"""Banner animado do topo do perfil, com uma decoração para cada tema.

As animações usam CSS (não SMIL) para respeitar prefers-reduced-motion.
As posições vêm de um gerador com semente fixa por dia, então o SVG só
muda quando o dia muda.
"""

import math
import random
from datetime import date
from html import escape

from temas import Tema, legivel

LARGURA, ALTURA = 1000, 330
FONTE = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace"


def _paleta(t: Tema) -> list[str]:
    cores = [c for _, c in t.stops()] + [t.acento, "ffffff"]
    return list(dict.fromkeys(legivel(c) for c in cores))


# --------------------------------------------------------------------------
# Decorações
# --------------------------------------------------------------------------

def _estrelas(rng: random.Random, t: Tema, n: int = 70) -> str:
    itens = []
    for _ in range(n):
        x, y = rng.uniform(0, LARGURA), rng.uniform(0, ALTURA)
        r = rng.choice((0.6, 0.9, 1.2, 1.7))
        itens.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" class="brilha" '
                     f'style="animation-duration:{rng.uniform(2, 5):.1f}s;animation-delay:-{rng.uniform(0, 5):.1f}s"/>')
    return "".join(itens)


def _queda(rng, n, forma, cores, dur=(7, 14), giro=False) -> str:
    itens = []
    for _ in range(n):
        x = rng.uniform(0, LARGURA)
        cor = rng.choice(cores)
        anima = f"animation-duration:{rng.uniform(*dur):.1f}s;animation-delay:-{rng.uniform(0, 14):.1f}s"
        deriva = rng.choice(("cai-e", "cai-d"))
        interno = forma(rng, cor)
        if giro:
            interno = (f'<g class="gira" style="animation-duration:{rng.uniform(1.5, 4):.1f}s">'
                       f"{interno}</g>")
        itens.append(f'<g transform="translate({x:.0f} -20)"><g class="{deriva}" style="{anima}">{interno}</g></g>')
    return "".join(itens)


def _neve(rng, t):
    floco = lambda rng, cor: f'<circle r="{rng.uniform(1.2, 3.2):.1f}" fill="#fff" opacity="{rng.uniform(.5, .95):.2f}"/>'
    return _queda(rng, 80, floco, ["fff"])


def _confete(rng, t):
    def peca(rng, cor):
        if rng.random() < 0.3:
            return f'<circle r="3" fill="#{cor}"/>'
        return f'<rect x="-3" y="-6" width="6" height="12" rx="1" fill="#{cor}"/>'
    return _queda(rng, 75, peca, _paleta(t), dur=(6, 11), giro=True)


def _coracoes(rng, t):
    itens, cores = [], _paleta(t)
    for _ in range(22):
        x, s = rng.uniform(0, LARGURA), rng.uniform(0.6, 1.4)
        itens.append(
            f'<g transform="translate({x:.0f} {ALTURA + 20}) scale({s:.2f})"><g class="sobe" '
            f'style="animation-duration:{rng.uniform(7, 13):.1f}s;animation-delay:-{rng.uniform(0, 13):.1f}s">'
            f'<path d="M0 4 C-8 -4 -12 4 0 12 C12 4 8 -4 0 4Z" fill="#{rng.choice(cores)}" opacity=".75"/></g></g>')
    return "".join(itens)


def _fogos(rng, t):
    itens, cores = [_estrelas(rng, t, 40)], _paleta(t)
    for i in range(6):
        cx, cy = rng.uniform(80, LARGURA - 80), rng.uniform(40, 170)
        cor, raio = rng.choice(cores), rng.uniform(40, 70)
        atraso = f"animation-delay:{i * 0.55:.2f}s"
        raios = "".join(
            f'<g transform="translate({cx:.0f} {cy:.0f}) rotate({a})">'
            f'<circle r="2.4" fill="#{cor}" class="explode" style="{atraso};--r:{raio:.0f}px"/></g>'
            for a in range(0, 360, 24))
        itens.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{raio * 0.5:.0f}" fill="#{cor}" class="clarao" style="{atraso}"/>{raios}')
    return "".join(itens)


def _bandeirinhas(rng, t):
    itens, cores = [_estrelas(rng, t, 35)], _paleta(t)
    for fio, (y0, flecha) in enumerate(((-4, 46), (-10, 80))):
        itens.append(f'<path d="M-10 {y0} Q{LARGURA / 2} {y0 + flecha * 2} {LARGURA + 10} {y0}" '
                     f'fill="none" stroke="#{t.acento}" stroke-opacity=".5"/>')
        for i in range(1, 24):
            p = i / 24
            x = (1 - p) ** 2 * -10 + 2 * (1 - p) * p * LARGURA / 2 + p ** 2 * (LARGURA + 10)
            y = (1 - p) ** 2 * y0 + 2 * (1 - p) * p * (y0 + flecha * 2) + p ** 2 * y0
            cor = cores[(i + fio) % len(cores)]
            itens.append(f'<g transform="translate({x:.0f} {y:.0f})"><path d="M-9 0 L9 0 L9 18 L0 12 L-9 18Z" '
                         f'fill="#{cor}" opacity=".85" class="balanca" '
                         f'style="animation-delay:-{rng.uniform(0, 3):.1f}s"/></g>')
    return "".join(itens)


def _matrix(rng, t):
    cor, itens = legivel(t.acento), []
    simbolos = "01アイウエオカキクケコサシスセソ<>/{}$#"
    for i in range(46):
        x = 10 + i * 22 + rng.uniform(-4, 4)
        coluna = "".join(
            f'<tspan x="0" dy="18"{" fill=&quot;#fff&quot;" if k == 13 else ""}>{escape(rng.choice(simbolos))}</tspan>'
            for k in range(14)).replace("&quot;", '"')
        itens.append(f'<g transform="translate({x:.0f} -260)"><text class="chove" fill="#{cor}" '
                     f'style="font-family:{MONO};font-size:14px;animation-duration:{rng.uniform(5, 10):.1f}s;'
                     f'animation-delay:-{rng.uniform(0, 10):.1f}s" opacity="{rng.uniform(.12, .32):.2f}">{coluna}</text></g>')
    return "".join(itens)


def _morcegos(rng, t):
    itens = [_estrelas(rng, t, 45),
             f'<circle cx="560" cy="70" r="70" fill="#fde68a" opacity=".08"/>'
             f'<circle cx="560" cy="70" r="30" fill="#fde68a" opacity=".9"/>'
             f'<circle cx="572" cy="62" r="26" fill="#0d1117" opacity=".35"/>']
    asa = "M0 0 C-6 -8 -16 -8 -22 -2 C-17 -2 -14 2 -13 5 C-9 1 -4 2 0 6 C4 2 9 1 13 5 C14 2 17 -2 22 -2 C16 -8 6 -8 0 0Z"
    for _ in range(9):
        y, s = rng.uniform(30, 220), rng.uniform(0.6, 1.3)
        itens.append(
            f'<g transform="translate(-40 {y:.0f}) scale({s:.2f})"><g class="voa" '
            f'style="animation-duration:{rng.uniform(9, 16):.1f}s;animation-delay:-{rng.uniform(0, 16):.1f}s">'
            f'<path d="{asa}" fill="#05050a" stroke="#{legivel(t.c2)}" stroke-opacity=".6" class="bate" '
            f'style="animation-delay:-{rng.uniform(0, .4):.2f}s"/></g></g>')
    return "".join(itens)


def _grade(rng, t):
    horizonte, itens = 215, []
    for i in range(-12, 13):
        itens.append(f'<line x1="{LARGURA / 2 + i * 28:.0f}" y1="{horizonte}" x2="{LARGURA / 2 + i * 150:.0f}" y2="{ALTURA}"/>')
    for k in range(1, 8):
        y = horizonte + (ALTURA - horizonte) * (k / 7) ** 1.8
        itens.append(f'<line x1="0" y1="{y:.0f}" x2="{LARGURA}" y2="{y:.0f}"/>')
    return (_estrelas(rng, t, 40)
            + f'<g stroke="#{t.c1}" stroke-opacity=".35">{"".join(itens)}</g>'
            + f'<rect x="0" y="0" width="{LARGURA}" height="2" fill="#{legivel(t.acento)}" opacity=".5" class="varre"/>')


def _emblema(cx: int, cy: int, hexagono: str) -> str:
    return (f'<polygon points="{hexagono}" fill="#0d1117" stroke="url(#grad)" stroke-width="3"/>'
            f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" style="font:800 34px {FONTE};letter-spacing:1px" '
            f'fill="url(#nome)">GBM</text>')


DECORACOES = {
    "estrelas": _estrelas, "neve": _neve, "confete": _confete,
    "coracoes": _coracoes, "fogos": _fogos, "bandeirinhas": _bandeirinhas,
    "matrix": _matrix, "morcegos": _morcegos, "grade": _grade,
}


# --------------------------------------------------------------------------

def _chips(rotulos: list[str], x: float, y: float, cores: list[str]) -> str:
    itens = []
    for i, rotulo in enumerate(rotulos):
        w = 22 + 7.4 * len(rotulo)
        cor = cores[i % len(cores)]
        itens.append(
            f'<g class="surge" style="animation-delay:{0.9 + i * 0.12:.2f}s">'
            f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="28" rx="14" fill="#{cor}" fill-opacity=".14" '
            f'stroke="#{cor}" stroke-opacity=".7"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + 18.5}" text-anchor="middle" '
            f'style="font:600 12.5px {FONTE};fill:#e2e8f0">{escape(rotulo)}</text></g>')
        x += w + 10
    return "".join(itens)


def banner(t: Tema, hoje: date, nome: str, subtitulo: str, comando: str, chips: list[str]) -> str:
    rng = random.Random(f"{hoje.isoformat()}-{t.chave}")
    c1, c2, acento = legivel(t.c1), legivel(t.c2), legivel(t.acento)
    decoracao = DECORACOES.get(t.decoracao, _estrelas)(rng, t)

    cx, cy = 840, 160
    hexagono = " ".join(f"{cx + 62 * math.cos(math.radians(a)):.1f},{cy + 62 * math.sin(math.radians(a)):.1f}"
                        for a in range(-90, 270, 60))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{LARGURA}" height="{ALTURA}" viewBox="0 0 {LARGURA} {ALTURA}" role="img" aria-label="{escape(nome)}: {escape(subtitulo)}">
  <title>{escape(nome)}: {escape(subtitulo)}</title>
  <style>
    .surge {{ animation: surgir .8s ease-out both; }}
    .brilha {{ animation: brilhar 3s ease-in-out infinite; }}
    .cai-e, .cai-d {{ animation: cai-e 10s linear infinite; }}
    .cai-d {{ animation-name: cai-d; }}
    .gira {{ animation: girar 3s linear infinite; transform-box: fill-box; transform-origin: center; }}
    .sobe {{ animation: subir 10s ease-in infinite; }}
    .explode {{ opacity: 0; animation: explodir 3.3s ease-out infinite; }}
    .clarao {{ opacity: 0; animation: clarear 3.3s ease-out infinite; }}
    .balanca {{ animation: balancar 3s ease-in-out infinite; transform-origin: 0 0; }}
    .chove {{ animation: chover 8s linear infinite; }}
    .voa {{ animation: voar 12s linear infinite; }}
    .bate {{ animation: bater .35s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: center; }}
    .varre {{ animation: varrer 6s linear infinite; }}
    .orbita {{ animation: girar 24s linear infinite; transform-origin: {cx}px {cy}px; }}
    .orbita-r {{ animation: girar 36s linear infinite reverse; transform-origin: {cx}px {cy}px; }}
    .cursor {{ animation: piscar 1s steps(1) infinite; }}
    .halo {{ animation: pulsar 5s ease-in-out infinite; transform-origin: {cx}px {cy}px; }}
    @keyframes surgir {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes brilhar {{ 0%, 100% {{ opacity: .15; }} 50% {{ opacity: .9; }} }}
    @keyframes cai-e {{ to {{ transform: translate(-40px, {ALTURA + 40}px); }} }}
    @keyframes cai-d {{ to {{ transform: translate(40px, {ALTURA + 40}px); }} }}
    @keyframes girar {{ to {{ transform: rotate(360deg); }} }}
    @keyframes subir {{ 0% {{ transform: translateY(0); opacity: 0; }} 15% {{ opacity: 1; }} 100% {{ transform: translateY(-{ALTURA + 60}px); opacity: 0; }} }}
    @keyframes explodir {{ 0%, 8% {{ opacity: 0; transform: translateX(0); }} 12% {{ opacity: 1; }} 55% {{ opacity: .9; transform: translateX(var(--r)); }} 75%, 100% {{ opacity: 0; transform: translateX(var(--r)) translateY(12px); }} }}
    @keyframes clarear {{ 0%, 8% {{ opacity: 0; }} 14% {{ opacity: .18; }} 40%, 100% {{ opacity: 0; }} }}
    @keyframes balancar {{ 0%, 100% {{ transform: rotate(-5deg); }} 50% {{ transform: rotate(5deg); }} }}
    @keyframes chover {{ to {{ transform: translateY({ALTURA + 260}px); }} }}
    @keyframes voar {{ to {{ transform: translate({LARGURA + 80}px, -40px); }} }}
    @keyframes bater {{ from {{ transform: scaleY(1); }} to {{ transform: scaleY(.35); }} }}
    @keyframes varrer {{ from {{ transform: translateY(0); }} to {{ transform: translateY({ALTURA}px); }} }}
    @keyframes piscar {{ 50% {{ opacity: 0; }} }}
    @keyframes pulsar {{ 0%, 100% {{ transform: scale(1); opacity: .55; }} 50% {{ transform: scale(1.08); opacity: .9; }} }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      {"".join(f'<stop offset="{o}%" stop-color="#{legivel(c)}"/>' for o, c in t.stops())}
    </linearGradient>
    <linearGradient id="nome" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff"/><stop offset="55%" stop-color="#ffffff"/><stop offset="100%" stop-color="#{acento}"/>
    </linearGradient>
    <radialGradient id="luz1"><stop offset="0%" stop-color="#{c1}" stop-opacity=".55"/><stop offset="100%" stop-color="#{c1}" stop-opacity="0"/></radialGradient>
    <radialGradient id="luz2"><stop offset="0%" stop-color="#{c2}" stop-opacity=".45"/><stop offset="100%" stop-color="#{c2}" stop-opacity="0"/></radialGradient>
    <pattern id="pontos" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#ffffff" opacity=".07"/></pattern>
    <clipPath id="card"><rect width="{LARGURA}" height="{ALTURA}" rx="16"/></clipPath>
  </defs>

  <g clip-path="url(#card)">
    <rect width="{LARGURA}" height="{ALTURA}" fill="#0d1117"/>
    <circle cx="130" cy="40" r="330" fill="url(#luz1)"/>
    <circle cx="{LARGURA - 90}" cy="{ALTURA}" r="320" fill="url(#luz2)"/>
    <rect width="{LARGURA}" height="{ALTURA}" fill="url(#pontos)"/>
    <g>{decoracao}</g>

    <g class="surge" style="animation-delay:.1s">
      <text x="60" y="88" style="font:500 16px {MONO};fill:#{acento}">{escape(comando)}<tspan class="cursor" fill="#ffffff">▌</tspan></text>
    </g>
    <g class="surge" style="animation-delay:.35s">
      <text x="57" y="152" style="font:800 56px {FONTE};letter-spacing:-1px" fill="url(#nome)">{escape(nome)}</text>
    </g>
    <g class="surge" style="animation-delay:.6s">
      <rect x="60" y="170" width="84" height="4" rx="2" fill="url(#grad)"/>
      <text x="60" y="207" style="font:500 20px {FONTE};fill:#e2e8f0">{escape(subtitulo)}</text>
    </g>
    {_chips(chips, 60, 240, [c1, c2, acento])}

    <g class="halo"><circle cx="{cx}" cy="{cy}" r="118" fill="url(#luz1)"/></g>
    <g class="orbita">
      <circle cx="{cx}" cy="{cy}" r="100" fill="none" stroke="#{c1}" stroke-width="1.5" stroke-dasharray="4 10" opacity=".8"/>
      <circle cx="{cx + 100}" cy="{cy}" r="5" fill="#{acento}"/>
    </g>
    <g class="orbita-r">
      <circle cx="{cx}" cy="{cy}" r="82" fill="none" stroke="#{c2}" stroke-width="1" stroke-dasharray="40 14" opacity=".7"/>
      <circle cx="{cx}" cy="{cy - 82}" r="3.5" fill="#{c2}"/>
    </g>
    {_emblema(cx, cy, hexagono)}

    <rect y="{ALTURA - 3}" width="{LARGURA}" height="3" fill="url(#grad)"/>
  </g>
  <rect x=".5" y=".5" width="{LARGURA - 1}" height="{ALTURA - 1}" rx="16" fill="none" stroke="#{c1}" stroke-opacity=".45"/>
</svg>
"""

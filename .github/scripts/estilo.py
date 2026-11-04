"""Base compartilhada pelos SVGs: fontes, cores neutras e a moldura dos cards."""

import html

from temas import Tema

FONTE = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Fira Code', Consolas, 'Courier New', monospace"
FUNDO, TEXTO, APAGADO = "0d1117", "e2e8f0", "8b949e"


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

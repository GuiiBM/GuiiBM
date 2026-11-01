"""Catálogo de temas sazonais do perfil.

Cada tema define quando fica ativo e as cores/textos usados no README, nos
cards SVG e na cobrinha. Quando duas datas se sobrepõem, vence o tema com a
maior prioridade (ex.: Halloween > Mês da Cibersegurança).

Para criar um tema novo, basta acrescentar um `Tema(...)` à lista TEMAS.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

# Aniversário no formato (mês, dia). Deixe None para desativar o tema.
ANIVERSARIO: tuple[int, int] | None = None


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


def ultima_sexta(ano: int, mes: int) -> date:
    proximo = date(ano + mes // 12, mes % 12 + 1, 1)
    d = proximo - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - 4) % 7)


def misturar(a: str, b: str, f: float) -> str:
    ca, cb = (tuple(int(x[i:i + 2], 16) for i in (0, 2, 4)) for x in (a, b))
    return "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(ca, cb))


def luminancia(cor: str) -> float:
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def legivel(cor: str) -> str:
    """Clareia cores escuras demais para aparecer sobre o fundo escuro."""
    return misturar(cor, "ffffff", 0.45) if luminancia(cor) < 60 else cor


def dia(mes: int, d: int) -> Callable[[int], tuple[date, date]]:
    return lambda ano: (date(ano, mes, d), date(ano, mes, d))


def periodo(m1: int, d1: int, m2: int, d2: int) -> Callable[[int], tuple[date, date]]:
    return lambda ano: (date(ano, m1, d1), date(ano, m2, d2))


@dataclass
class Tema:
    chave: str
    nome: str
    emoji: str
    prioridade: int
    quando: Callable[[int], tuple[date, date]] | None
    c1: str                      # cor principal
    c2: str                      # cor secundária
    acento: str                  # destaques (títulos, números)
    descricao: str               # subtítulo do banner
    saudacao: str | None = None  # primeira linha do texto digitado
    trofeu: str = "dracula"
    perfil3d: str = "profile-night-rainbow.svg"
    animacao: str = "twinkling"
    # Efeito do banner: estrelas, neve, fogos, confete, coracoes,
    # bandeirinhas, matrix, morcegos ou grade.
    decoracao: str = "estrelas"
    gradiente: list[tuple[int, str]] = field(default_factory=list)

    def periodos(self, ano: int) -> list[tuple[date, date]]:
        if self.quando is None:
            return []
        inicio, fim = self.quando(ano)
        if fim < inicio:  # período que vira o ano (ex.: 31/12 a 02/01)
            return [(date(ano - 1, inicio.month, inicio.day), fim),
                    (inicio, date(ano + 1, fim.month, fim.day))]
        return [(inicio, fim)]

    def ativo(self, hoje: date) -> bool:
        return any(i <= hoje <= f for i, f in self.periodos(hoje.year))

    def stops(self) -> list[tuple[int, str]]:
        return self.gradiente or [(0, self.c1), (100, self.c2)]


PADRAO = Tema(
    "padrao", "Cyberpunk", "⚡", 0, None,
    c1="7e22ce", c2="ef4444", acento="a855f7",
    descricao="Offensive Security | Red Team | Web Dev",
)

TEMAS: list[Tema] = [
    Tema("ano_novo", "Ano Novo", "🎆", 2, periodo(12, 31, 1, 2),
         c1="f59e0b", c2="1e3a8a", acento="fbbf24",
         descricao="Feliz {ano_novo}! | Offensive Security | Red Team",
         decoracao="fogos",
         saudacao="🎆 Feliz {ano_novo}! Bora pra mais um ano de código",
         trofeu="radical", animacao="blink",
         gradiente=[(0, "f59e0b"), (55, "b45309"), (100, "1e3a8a")]),
    Tema("protecao_dados", "Dia da Proteção de Dados", "🔐", 3, dia(1, 28),
         c1="0f766e", c2="22d3ee", acento="2dd4bf",
         descricao="Data Privacy Day | Offensive Security | Red Team",
         decoracao="grade",
         saudacao="🔐 28/01: Dia Internacional da Proteção de Dados",
         trofeu="nord"),
    Tema("carnaval", "Carnaval", "🎭", 2,
         lambda ano: (pascoa(ano) - timedelta(days=51), pascoa(ano) - timedelta(days=46)),
         c1="db2777", c2="facc15", acento="f472b6",
         descricao="Carnaval | Offensive Security | Red Team",
         decoracao="confete",
         saudacao="🎭 Carnaval: confete, serpentina e commits",
         trofeu="radical", animacao="blinking",
         gradiente=[(0, "db2777"), (50, "facc15"), (100, "16a34a")]),
    Tema("mulher", "Dia Internacional da Mulher", "💜", 3, dia(3, 8),
         c1="9333ea", c2="f0abfc", acento="c084fc",
         descricao="Dia Internacional da Mulher | Offensive Security",
         decoracao="coracoes",
         saudacao="💜 Viva as mulheres na tecnologia e na segurança",
         trofeu="dracula"),
    Tema("pascoa", "Páscoa", "🐰", 2,
         lambda ano: (pascoa(ano) - timedelta(days=2), pascoa(ano)),
         c1="92400e", c2="f9a8d4", acento="f59e0b",
         descricao="Feliz Páscoa | Offensive Security | Red Team",
         decoracao="confete",
         saudacao="🐰 Feliz Páscoa! Caçando ovos (e bugs)",
         trofeu="gruvbox", perfil3d="profile-south-season-animate.svg"),
    Tema("star_wars", "Star Wars Day", "⚔️", 3, dia(5, 4),
         c1="facc15", c2="0f172a", acento="facc15",
         descricao="May the 4th be with you | Offensive Security",
         decoracao="estrelas",
         saudacao="⚔️ May the 4th be with you",
         trofeu="darkhub", perfil3d="profile-night-view.svg"),
    Tema("namorados", "Dia dos Namorados", "❤️", 3, dia(6, 12),
         c1="e11d48", c2="f472b6", acento="fb7185",
         descricao="Dia dos Namorados | Offensive Security | Red Team",
         decoracao="coracoes",
         saudacao="❤️ Hoje o código é escrito com <3",
         trofeu="radical"),
    Tema("junina", "Festa Junina", "🌽", 2, periodo(6, 13, 6, 29),
         c1="ea580c", c2="facc15", acento="fb923c",
         descricao="Arraiá do GuiiBM | Offensive Security | Red Team",
         decoracao="bandeirinhas",
         saudacao="🌽 Arraiá do GuiiBM: olha a cobra! (é mentira)",
         trofeu="gruvbox", perfil3d="profile-south-season-animate.svg",
         gradiente=[(0, "dc2626"), (35, "ea580c"), (70, "facc15"), (100, "2563eb")]),
    Tema("orgulho", "Orgulho LGBTQIA+", "🏳️‍🌈", 3, dia(6, 28),
         c1="8b5cf6", c2="ef4444", acento="a78bfa",
         descricao="Dia do Orgulho LGBTQIA+ | Offensive Security",
         decoracao="confete",
         saudacao="🏳️‍🌈 Tecnologia é feita por todo mundo",
         trofeu="radical",
         gradiente=[(0, "e40303"), (20, "ff8c00"), (40, "ffed00"),
                    (60, "008026"), (80, "004dff"), (100, "750787")]),
    Tema("sysadmin", "Dia do SysAdmin", "🖥️", 3, lambda ano: (ultima_sexta(ano, 7),) * 2,
         c1="2563eb", c2="22d3ee", acento="60a5fa",
         descricao="SysAdmin Day | Offensive Security | Red Team",
         decoracao="grade",
         saudacao="🖥️ Feliz Dia do SysAdmin: uptime é amor",
         trofeu="tokyonight"),
    Tema("independencia", "Independência do Brasil", "🇧🇷", 3, dia(9, 7),
         c1="16a34a", c2="facc15", acento="22c55e",
         descricao="7 de Setembro | Offensive Security | Red Team",
         decoracao="confete",
         saudacao="🇧🇷 7 de Setembro: Independência do Brasil",
         trofeu="onedark", perfil3d="profile-night-green.svg",
         gradiente=[(0, "16a34a"), (60, "facc15"), (100, "1d4ed8")]),
    Tema("programador", "Dia do Programador", "🧑‍💻", 3,
         lambda ano: (date(ano, 1, 1) + timedelta(days=255),) * 2,
         c1="16a34a", c2="052e16", acento="4ade80",
         descricao="Dia do Programador (0x100) | Offensive Security",
         decoracao="matrix",
         saudacao="🧑‍💻 Feliz Dia do Programador! (dia 0x100 do ano)",
         trofeu="matrix", perfil3d="profile-night-green.svg", animacao="blink"),
    Tema("ciberseguranca", "Mês da Cibersegurança", "🛡️", 1, periodo(10, 1, 10, 31),
         c1="0ea5e9", c2="7e22ce", acento="38bdf8",
         descricao="Cybersecurity Awareness Month | Red Team",
         decoracao="grade",
         saudacao="🛡️ Outubro: Mês da Conscientização em Cibersegurança",
         trofeu="tokyonight", perfil3d="profile-night-view.svg"),
    Tema("criancas", "Dia das Crianças", "🧸", 3, dia(10, 12),
         c1="f97316", c2="3b82f6", acento="fb923c",
         descricao="Dia das Crianças | Offensive Security | Red Team",
         decoracao="confete",
         saudacao="🧸 Todo hacker começou desmontando alguma coisa",
         trofeu="radical",
         gradiente=[(0, "f97316"), (50, "facc15"), (100, "3b82f6")]),
    Tema("halloween", "Halloween", "🎃", 2, periodo(10, 24, 10, 31),
         c1="f97316", c2="fdba74", acento="fb923c",
         descricao="Happy Halloween | Offensive Security | Red Team",
         decoracao="morcegos",
         saudacao="🎃 Happy Halloween! Doces ou exploits?",
         trofeu="dark_lover", perfil3d="profile-night-view.svg",
         animacao="fadeIn",
         gradiente=[(0, "c2410c"), (50, "f97316"), (100, "fdba74")]),
    Tema("consciencia_negra", "Dia da Consciência Negra", "✊🏿", 3, dia(11, 20),
         c1="ca8a04", c2="15803d", acento="eab308",
         descricao="Dia da Consciência Negra | Offensive Security",
         decoracao="estrelas",
         saudacao="✊🏿 20/11: Dia da Consciência Negra",
         trofeu="gruvbox",
         gradiente=[(0, "15803d"), (50, "ca8a04"), (100, "b91c1c")]),
    Tema("seguranca_info", "Dia da Segurança da Informação", "🛡️", 3, dia(11, 30),
         c1="06b6d4", c2="7e22ce", acento="22d3ee",
         descricao="Computer Security Day | Offensive Security",
         decoracao="grade",
         saudacao="🛡️ 30/11: Dia Internacional da Segurança da Informação",
         trofeu="tokyonight", perfil3d="profile-night-view.svg"),
    Tema("natal", "Natal", "🎄", 2, periodo(12, 1, 12, 30),
         c1="dc2626", c2="f8fafc", acento="f87171",
         descricao="Boas Festas | Offensive Security | Red Team",
         decoracao="neve",
         saudacao="🎄 Boas festas! Ho-ho-ho, git push",
         trofeu="monokai", perfil3d="profile-night-view.svg",
         gradiente=[(0, "dc2626"), (50, "f8fafc"), (100, "dc2626")]),
]

if ANIVERSARIO:
    TEMAS.append(Tema(
        "aniversario", "Aniversário", "🎂", 4, dia(*ANIVERSARIO),
        c1="ec4899", c2="8b5cf6", acento="f472b6",
        descricao="Hoje é meu aniversário! | Offensive Security",
        decoracao="confete",
        saudacao="🎂 Hoje é meu aniversário!",
        trofeu="radical", animacao="blinking",
    ))


def tema_do_dia(hoje: date) -> Tema:
    ativos = [t for t in TEMAS if t.ativo(hoje)]
    return max(ativos, key=lambda t: t.prioridade) if ativos else PADRAO

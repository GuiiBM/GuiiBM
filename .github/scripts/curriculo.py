"""Dados do currículo (Lattes) e do portfólio exibidos no README.

Edite as listas abaixo quando o Lattes mudar: o push dispara o workflow, que
reescreve os blocos <!-- auto:... --> do README e redesenha a linha do tempo.
Telefone, endereço e e-mail pessoal ficam de fora de propósito: o README é público.
"""

LATTES = "http://lattes.cnpq.br/9693803343170549"
ORCID = "https://orcid.org/0009-0007-4614-9029"

# (período, cargo, instituição, vínculo, [atividades])
EXPERIENCIA = [
    ("2026 · atual", "Bolsista de Pesquisa e Desenvolvimento (PIBICT)", "Fatec São Sebastião · CEETEPS",
     "Bolsista · 12h semanais", [
         "Investigação, modelagem e implementação de integrações seguras de agendamento e notificação com o e-SUS PEC, usando a API do WhatsApp (Meta Business Platform).",
         "Mecanismos automatizados de contingência para falhas de comunicação, tratamento de exceções em tempo real e resiliência na entrega de mensagens críticas de saúde.",
         "Arquitetura orientada a serviços, consumo de APIs RESTful e análise de requisitos de segurança de dados e privacidade em sistemas públicos de saúde.",
     ]),
    ("2026 · atual", "Projeto de Inclusão Digital para a Comunidade", "CEETEPS (extensão)",
     "Bolsista de extensão", [
         "Ensino de informática básica e ferramentas digitais para a comunidade.",
         "Apoio à gestão, planejamento pedagógico, divulgação e marketing do curso.",
         "Monitoria presencial em sala de aula.",
     ]),
    ("2024 · 2025", "Estagiário Técnico em Informática", "FUNDART · Fundação de Arte e Cultura de Ubatuba",
     "Estágio · 30h semanais", [
         "Suporte técnico presencial e remoto: formatação e manutenção de computadores, softwares corporativos, e-mails institucionais, redes e impressoras.",
         "Diagnóstico e manutenção de hardware, roteadores, switches e cabeamento estruturado.",
         "Inventário de hardware e software e manuais de uso para os funcionários.",
         "Desenvolvimento de um sistema próprio de suporte transitório para o controle da Biblioteca Municipal.",
         "Levantamento de requisitos, ETP, Termo de Referência e avaliação de Prova de Conceito para contratar e migrar o sistema definitivo em nuvem (SaaS).",
     ]),
    ("2022 · 2025", "Iniciação Científica Júnior (PIC-OBMEP)", "IMPA · CNPq",
     "Bolsista · 10h semanais", [
         "Participação consecutiva nas edições 16, 17, 18 e 19 do programa, com bolsa do CNPq.",
         "Matemática avançada, raciocínio lógico, análise combinatória, teoria dos números, geometria e resolução de problemas.",
     ]),
]

# Barras da linha do tempo: (rótulo, início, fim, faixa). Fim None = até hoje;
# o fim é exclusivo (2026 significa até o fim de 2025).
LINHA_DO_TEMPO = [
    ("Ubatubasat: eletrônica e programação", 2019, 2025, "formacao"),
    ("PIC-OBMEP · IMPA", 2022, 2026, "pesquisa"),
    ("Técnico em Informática + Ensino Médio", 2023, 2026, "formacao"),
    ("Estágio de TI · FUNDART", 2024, 2026, "trabalho"),
    ("ADS · Fatec São Sebastião", 2026, None, "formacao"),
    ("Pesquisa PIBICT · e-SUS PEC + API Meta", 2026, None, "pesquisa"),
    ("Extensão: Inclusão Digital", 2026, None, "trabalho"),
]

# (período, título, situação, coordenação, financiamento, descrição)
PESQUISA = [
    ("2026 · atual",
     "Modernização da Gestão de Fluxos e Agendamentos na Atenção Primária à Saúde de São Sebastião",
     "Em andamento", "Douglas Fabiano Lourenço", "PIBICT · CEETEPS",
     "Integração segura ao e-SUS PEC via API Meta e mecanismos de contingência automatizados, "
     "para otimizar e automatizar agendamentos e fluxos de atendimento."),
    ("2022 · 2025",
     "Programa de Iniciação Científica Júnior: PIC/OBMEP",
     "Concluído", "Reinaldo Gen Ichiro Arakaki", "Bolsa CNPq",
     "Desenvolvimento de aptidões em matemática avançada, raciocínio lógico, análise combinatória, "
     "teoria dos números e geometria, em programa promovido pelo IMPA."),
]

CITACAO = ("MACHADO, G. B.; LOURENCO, D. F. Modernização da Gestão de Fluxos e Agendamentos na Atenção "
           "Primária à Saúde de São Sebastião: Integração Segura ao e-SUS PEC via API Meta e Mecanismos de "
           "Contingência Automatizados. In: Seminário de Inovação, Ciência e Tecnologia do Litoral Norte, "
           "2026, Caraguatatuba. Anais [...]. Caraguatatuba: IFSP Campus Caraguatatuba, 2026.")

# (ano, título, tipo)
PRODUCAO_TECNICA = [
    ("2026", "Rosto a Rosto", "Consultoria de aplicações web"),
    ("2025", "Infraestrutura web, dashboards financeiros/contábeis e soluções digitais para PMEs", "Consultoria de aplicações web"),
    ("2025", "Sistema Automatizado de Gestão e Controle de Empréstimos: Biblioteca Municipal (FUNDART)", "Aplicação web, serviço interno"),
    ("2024", "ETP, Termo de Referência e avaliação de PoC para software de gestão de biblioteca municipal (com M. F. Aranha)", "Trabalho técnico, assessoramento"),
]

# (período, curso, instituição)
FORMACAO = [
    ("2026 · atual", "Análise e Desenvolvimento de Sistemas (graduação)", "Fatec São Sebastião · CEETEPS"),
    ("2023 · 2025", "Técnico em Informática", "EM Pres. Tancredo de Almeida Neves"),
    ("2023 · 2025", "Ensino Médio", "EM Pres. Tancredo de Almeida Neves"),
]

# Grupo -> [(ano, curso, instituição, horas ou None)]
CURSOS = {
    "🛡️ Cibersegurança": [
        ("2026", "Introduction to Information Security (Edital ARI 004/2026)", "CEETEPS", 40),
        ("2026", "Cibersegurança: Segurança da Informação e Ataques Cibernéticos", "USP", 8),
        ("2026", "Introduction to Cybersecurity", "Cisco Networking Academy", None),
        ("2026", "Sensibilização para a Segurança Digital", "Cisco Networking Academy", None),
        ("2026", "Mundo Conectado: Manual de Sobrevivência", "ENAP", 10),
    ],
    "💻 Programação e tecnologia": [
        ("2026", "Introduction to the C Programming Language (Edital ARI 027/2026)", "CEETEPS", 40),
        ("2026", "Conexão Game Jam 2026", "CEETEPS", 8),
        ("2026", "Criptomoedas e Blockchain: Fundamentos, Mercado e Primeiros Passos", "USP", 8),
        ("2026", "The Hour of A.I.", "Code.org", None),
        ("2025 · 2026", "Tech Mentoring: Mentoria Técnica Profissional", "Vinicius Senger", None),
    ],
    "🛰️ Ubatubasat: eletrônica e programação": [
        ("2024", "Módulo 6: Eletrônica e Programação", "EM Pres. Tancredo de Almeida Neves", 90),
        ("2023", "Módulo 5: Eletrônica e Programação", "EM Pres. Tancredo de Almeida Neves", 90),
        ("2022", "Módulo 4: Eletrônica e Programação", "EM Pres. Tancredo de Almeida Neves", 90),
        ("2021", "Módulo 3: Eletrônica e Programação", "EM Pres. Tancredo de Almeida Neves", 90),
        ("2020", "Módulo 2: Eletrônica Básica", "EM Pres. Tancredo de Almeida Neves", 90),
        ("2019", "Módulo 1: Eletrônica Básica", "EM Pres. Tancredo de Almeida Neves", 90),
    ],
    "🌐 Idiomas e design": [
        ("2024 · 2025", "Inglês: nível intermediário (B1)", "CCAA", 152),
        ("2024", "Fundamentos do Design Gráfico", "Fundação Bradesco", 6),
    ],
}

# (idioma, compreende, fala, lê, escreve)
IDIOMAS = [
    ("Português", "Bem", "Bem", "Bem", "Bem"),
    ("Inglês", "Bem", "Razoavelmente", "Bem", "Razoavelmente"),
]

# (ano, título, detalhe, nível) — nível define a medalha: ouro, prata, bronze ou marca
PREMIOS = [
    ("2026", "1º lugar na 1ª Litoral Game Jam", "6ª Expo Game Jam · Fatec, polo São Sebastião", "ouro"),
    ("2026", "Aprovação na avaliação teórica de Piloto de Drone (RPAS)", "ANAC", "marca"),
    ("2026", "Proficiência em Aviation English Level 3", "STP TRAINAIR PLUS OACI · ANAC", "marca"),
    ("2026", "Resumo publicado e apresentado no SICLN 2026", "IFSP Caraguatatuba · e-SUS PEC + API Meta", "marca"),
    ("2026", "Avaliação técnica e arbitragem na OBR", "Olimpíada Brasileira de Robótica · etapa regional", "marca"),
    ("2025", "Menção Honrosa na 20ª OBMEP", "IMPA", "prata"),
    ("2024", "Menção Honrosa na 19ª OBMEP", "IMPA", "prata"),
    ("2023", "Menção Honrosa na 18ª OBMEP", "IMPA", "prata"),
    ("2023", "Menção Honrosa na 3ª Olimpíada Mandacaru de Matemática", "Comitê Organizador", "prata"),
    ("2021", "Medalha de Bronze na 16ª OBMEP", "IMPA", "bronze"),
]

# (ano, evento, tipo)
EVENTOS = [
    ("2026", "1ª Conexão Game Jam · 1ª Litoral Game Jam · 6ª Expo Game Jam, com os jogos Paradoxo de Wilson e Rosto a Rosto", "Feira"),
    ("2026", "Seminário de Inovação, Ciência e Tecnologia do Litoral Norte (SICLN 2026)", "Simpósio"),
    ("2026", "5º Encontro do Clube da Robótica", "Seminário"),
    ("2025", "The Developer's Conference (TDC 2025)", "Congresso"),
    ("2025", "OBMEP 2025", "Olimpíada"),
    ("2024", "OBMEP 2024", "Olimpíada"),
    ("2024", "Olimpíada Brasileira de Astronomia e Astronáutica (OBA 2024)", "Olimpíada"),
    ("2023", "OBMEP 2023", "Olimpíada"),
    ("2023", "Olimpíada Mandacaru de Matemática (3ª edição)", "Olimpíada"),
    ("2022", "OBMEP 2022", "Olimpíada"),
    ("2022", "Olimpíada Brasileira de Astronomia e Astronáutica (OBA 2022)", "Olimpíada"),
    ("2021", "OBMEP 2021", "Olimpíada"),
]

# Destaques: (título, repositório, resumo, stack, site ou None)
DESTAQUES = [
    ("Verto", "Verto-Multi-purpose-Media-Security-Processing-Suite",
     "Suíte local-first com 40 ferramentas de IA, criptografia, binários e mídia. Os dados sensíveis ficam na máquina do usuário.",
     ["Python", "Flask", "Demucs", "rembg", "faster-whisper", "AES-256", "yt-dlp"], None),
    ("Massive OSINT Framework", "Massive-OSINT-Communication-Framework",
     "Coleta de dados públicos (OSINT) em múltiplas fontes e automação de comunicação via WhatsApp Web.",
     ["Python", "Selenium", "BeautifulSoup4", "Pandas", "Pillow"], None),
    ("Ressonance", "Ressonance",
     "Plataforma de música com um algoritmo diferente, com APIs REST e player próprio.",
     ["PHP", "JavaScript", "APIs REST"], "https://ressonance.hyperphp.com/"),
    ("Regulador Financeiro", "reguladorfinanceiro",
     "Monitoramento de mercado com atraso de 15 min: ações e FIIs, carteira, recomendações, análise técnica e dividendos.",
     ["Python", "Flask", "SQLite", "yfinance", "pandas", "APScheduler"], None),
    ("Calcula Passagem", "CalcularPassagens",
     "Soma as viagens de ônibus entre Ubatuba, Caraguatatuba e São Sebastião e mostra quanto colocar no cartão.",
     ["HTML", "JavaScript", "Netlify"], "https://calcularpassagens.netlify.app/"),
    ("Mundo Ágape", "MundoAgape",
     "Site do ministério infantil da Igreja Ágape, com lições, fotos, eventos e recursos em um só lugar.",
     ["HTML", "CSS", "JavaScript"], "https://mundoagape.netlify.app/"),
]

# Portfólio (gbm-mkt.netlify.app)
SERVICOS = ["Desenvolvimento Web", "Design Visual", "Programação", "Gerenciamento de Conteúdo",
            "Prototipagem Digital", "Design UI/UX", "Design Gráfico", "Edição de Imagens"]
PROJETOS_ENTREGUES = 30
# (perfil, nome, trabalho)
PERFIS = [
    ("gbm_mkt", "GBM Marketing Digital", "Perfil oficial, com cases e novidades"),
    ("loc_andaimes_", "Loc Andaimes", "Gerenciamento completo do Instagram"),
    ("junior.bgouvea", "Reginaldo Bueno de Gouvêa Junior", "Posts, iLinks e website"),
    ("felipej.consultor", "Felipe João", "Posts e iLinks"),
    ("twbteacherwillians", "Teacher Willians Batistela", "Posts de divulgação de cursos e aulas"),
    ("oliveira_bicicletaria", "Bicicletaria Oliveira", "Posts desenvolvidos pela GBM"),
]


def total_cursos() -> int:
    return sum(len(lista) for lista in CURSOS.values())


def total_horas() -> int:
    return sum(horas or 0 for lista in CURSOS.values() for *_, horas in lista)

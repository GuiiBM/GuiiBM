"""Dados do currículo (Lattes) exibidos no README, como texto e tabelas.

Edite as listas abaixo quando o Lattes mudar: o push dispara o workflow, que
reescreve os blocos <!-- auto:... --> do README sozinho.
"""

LATTES = "http://lattes.cnpq.br/9693803343170549"
ORCID = "https://orcid.org/0009-0007-4614-9029"

# (período, cargo, instituição, descrição)
TRAJETORIA = [
    ("2026 · atual", "Bolsista de Pesquisa (PIBICT)", "Fatec São Sebastião · CEETEPS",
     "Integração segura do e-SUS PEC com a API do WhatsApp (Meta) para agendamentos na "
     "Atenção Primária à Saúde, com mecanismos de contingência automatizados."),
    ("2026 · atual", "Extensão: Inclusão Digital", "CEETEPS",
     "Monitoria em sala, planejamento pedagógico e divulgação de um curso de informática "
     "básica para a comunidade."),
    ("2024 · 2025", "Estagiário Técnico em Informática", "FUNDART",
     "Suporte, redes e infraestrutura de TI; sistema próprio de controle da Biblioteca "
     "Municipal; ETP, Termo de Referência e PoC para contratação de software SaaS."),
    ("2022 · 2025", "Iniciação Científica Júnior", "PIC-OBMEP · IMPA · CNPq",
     "Quatro edições seguidas (16ª a 19ª) com bolsa do CNPq: matemática avançada, lógica "
     "e resolução de problemas."),
]

# (período, curso, instituição)
FORMACAO = [
    ("2026 · atual", "Análise e Desenvolvimento de Sistemas", "Fatec São Sebastião · CEETEPS"),
    ("2023 · 2025", "Técnico em Informática", "EM Pres. Tancredo de Almeida Neves"),
]

# (ano, certificação, instituição)
CERTIFICACOES = [
    ("2026", "Introduction to Cybersecurity", "Cisco Networking Academy"),
    ("2026", "Cibersegurança e Ataques Cibernéticos", "USP"),
    ("2026", "Introduction to Information Security (40h)", "CEETEPS"),
    ("2026", "Introduction to the C Programming Language (40h)", "CEETEPS"),
    ("2025", "Inglês intermediário B1 (152h)", "CCAA"),
]

# (ano, título, detalhe, nível) — nível define a medalha: ouro, prata, bronze ou marca
PREMIOS = [
    ("2026", "1º lugar na 1ª Litoral Game Jam", "6ª Expo Game Jam · Fatec", "ouro"),
    ("2021", "Medalha de Bronze na OBMEP", "16ª edição · IMPA", "bronze"),
    ("2023 · 2025", "3 Menções Honrosas na OBMEP", "18ª, 19ª e 20ª edições · IMPA", "prata"),
    ("2023", "Menção Honrosa na Olimpíada Mandacaru", "3ª edição · Matemática", "prata"),
    ("2026", "Resumo publicado no SICLN 2026", "IFSP Caraguatatuba · e-SUS PEC + API Meta", "marca"),
    ("2026", "Avaliador e árbitro na OBR", "Olimpíada Brasileira de Robótica · Regional", "marca"),
    ("2026", "Piloto de Drone (RPAS): prova teórica", "ANAC", "marca"),
    ("2026", "Aviation English Level 3", "ANAC · OACI TRAINAIR PLUS", "marca"),
]

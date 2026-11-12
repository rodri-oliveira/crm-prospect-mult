"""Legacy segment vocabularies, kept unchanged during extraction."""

_INFO_NOISE_NAMES = [
    "escola de",
    "curso",
    "treinamento",
    "baterias",
    "bateria",
    "automotiva",
    "centro automotivo",
    "nuvem",
    "cloud",
    "software",
    "sistemas",
    "consultoria",
    "material eletrico",
    "eletrica",
    "hidraulica",
    "moveis para escritorio",
    "servicos de ti",
    "desentupidora",
    "provedor",
    "internet service provider",
    "software company",
    "data recovery service",
    "telecom",
    "telecomunicacoes",
    "telecomunicações",
    "fibra",
    "provedor de internet",
    "telecommunications service provider",
    "cftv",
    "segurança",
    "seguranca",
    "security system supplier",
    "cerca eletrica",
    "portão",
]


_BRINQUEDOS_POSITIVE_TERMS = [
    "brinquedo",
    "brinquedos",
    "toy store",
    "loja de brinquedos",
    "distribuidor de brinquedos",
    "atacadista de brinquedos",
    "atacado de brinquedos",
    "revenda de brinquedos",
    "importadora de brinquedos",
    "brinquedos educativos",
    "jogos educativos",
    "jogos infantis",
    "artigos infantis",
    "loja infantil",
    "loja kids",
    "baby store",
    "bebe e brinquedos",
    "crianca e brinquedos",
]


_BRINQUEDOS_NOISE_NAMES = [
    "buffet",
    "festa",
    "festas",
    "decoracao",
    "decoracoes",
    "locacao",
    "locadora",
    "aluguel",
    "aluga",
    "recreacao",
    "animacao",
    "animador",
    "playground",
    "parque",
    "brinquedoteca",
    "escola",
    "creche",
    "bercario",
    "curso",
    "terapia",
    "clinica",
    "odontopediatria",
    "fotografia",
    "estudio fotografico",
    "roupa infantil",
    "moda infantil",
    "calcados infantis",
    "enxoval",
    "maternidade",
    "fralda",
    "fraldas",
    "salao infantil",
    "cabelo infantil",
]


_GAMER_NOISE_NAMES = [
    "lan house",
    "lanhouse",
    "cyber cafe",
    "cybercafe",
    "arena e-sports",
    "arena esports",
    "arena gamer",
    "salao de jogos",
    "salao de games",
    "clube de jogos",
    "clube de games",
    "fliperama",
    "fliperamas",
    "sinuca",
    "bilhar",
    "boliche",
    "escape room",
    "casa de jogos",
    "cassino",
    "poker",
    "baralho",
    "jogos de azar",
]


_SENNHEISER_NOISE_NAMES = [
    "som automotivo",
    "audio automotivo",
    "audio car",
    "acessorios para carro",
    "acessorios automotivos",
    "central multimidia",
    "dvd automotivo",
    "som residencial",
    "home theater",
    "home cinema",
    "conserto de tv",
    "conserto de radio",
    "assistencia tecnica",
    "assistencia eletronica",
    "reparo eletronico",
    "manutencao eletronica",
    "eletronica de bairro",
    "alto falante de carro",
    "alto falante automotivo",
    "alarme automotivo",
    "insulfilm",
    "pelicula",
    "envelopamento",
    "sound e film",
    "sound & film",
    "som e film",
    "som & film",
    "auto som",
    "sound car",
]


_SENNHEISER_BUYER_PROFILE_TERMS = [
    "audio profissional",
    "pro audio",
    "loja de audio",
    "instrumentos musicais",
    "microfone",
    "microfones",
    "fone profissional",
    "equipamentos de som",
    "estudio",
    "gravacao",
    "podcast",
    "produtora",
    "audiovisual",
    "radio",
    "tv",
    "broadcast",
    "igreja",
    "templo",
    "auditorio",
    "teatro",
    "casa de show",
    "centro de convencoes",
    "casa de eventos",
    "hotel",
    "universidade",
    "escola de musica",
    "sonorizacao",
    "locacao de som",
    "locadora de som",
    "eventos",
    "integrador",
    "audio e video",
    "videoconferencia",
    "conferencia",
    "corporativo",
]


_SENNHEISER_STRONG_QUERY_TERMS = [
    "broadcast audio",
    "emissora de radio",
    "emissora de tv",
    "estudio de gravacao",
    "estudio de podcast",
    "produtora audiovisual",
    "produtora de video",
    "som para igreja",
    "sonorizacao para igrejas",
    "sonorizacao de eventos",
    "locadora de som",
    "locacao de som para eventos",
    "loja de instrumentos musicais",
    "loja de audio profissional",
    "revenda de audio profissional",
    "distribuidor de instrumentos musicais",
    "revenda de instrumentos musicais",
    "integrador audio e video",
    "integrador av",
    "audio corporativo",
    "sistemas de conferencia",
]


_SENNHEISER_HIGH_INTENT_TERMS = [
    "podcast",
    "estudio",
    "gravacao",
    "radio",
    "emissora",
    "broadcast",
    "loja de audio",
    "audio profissional",
    "instrumentos musicais",
    "escola de musica",
    "conservatorio",
    "microfone",
    "microfones",
    "sonorizacao",
    "locadora de som",
    "locacao de som",
    "integrador audio",
    "integrador av",
]


_SENNHEISER_MEDIUM_INTENT_TERMS = [
    "produtora",
    "audiovisual",
    "foto video",
    "film",
    "eventos",
    "casa de eventos",
    "centro de convencoes",
    "anfiteatro",
    "auditorio",
    "teatro",
    "casa de show",
    "igreja",
    "templo",
    "hotel",
    "universidade",
    "videoconferencia",
    "conferencia",
    "corporativo",
]


_SENNHEISER_LOW_CONFIDENCE_TERMS = [
    "recanto",
    "chacara",
    "sitio",
    "espaco",
    "salao de festas",
    "festa infantil",
    "buffet infantil",
    "casa da alegria",
]


_SENNHEISER_BUSINESS_HINTS = [
    "radio",
    "fm",
    "studio",
    "estudio",
    "podcast",
    "music",
    "musical",
    "som",
    "sound",
    "audio",
    "video",
    "film",
    "eventos",
    "producoes",
    "produtora",
    "igreja",
    "conservatorio",
    "instituto",
    "escola",
    "teatro",
    "anfiteatro",
    "eventos",
]


_INFO_POSITIVE_TERMS = [
    "informatica", "informática", "perifericos", "periféricos", "hardware",
    "suprimentos", "computador", "computadores", "notebook", "notebooks",
    "laptop", "laptops", "nobreak", "nobreaks", "cabos", "conectores",
    "mouse", "mouses", "teclado", "teclados", "pendrive", "ssd",
    "memoria", "memória", "componentes", "papelaria", "eletronicos", "eletrônicos",
    "computer", "electronics", "office supply", "tech", "technology",
]


_PERSONAL_FIRST_NAMES = {
    "joao", "joão", "pedro", "carlos", "paulo", "jose", "josé", "maria",
    "lucas", "gabriel", "matheus", "marcos", "andre", "andré", "felipe",
    "rafael", "luiz", "luis", "rodrigo", "diego", "bruno", "eduardo",
    "guilherme", "renato", "marcelo", "alexandre", "fernando", "ricardo",
    "vitor", "victor", "tiago", "thiago", "claudio", "cláudio", "sergio",
    "sérgio", "antonio", "antônio", "francisco", "mario", "mário"
}


_BUSINESS_INDICATORS = [
    "distribuidora", "distribuidor", "revenda", "atacado", "atacadista",
    "suprimentos", "comercio", "comércio", "comercial", "loja", "store",
    "milenio", "milênio", "alpha", "beta", "tech", "pc", "eletronica",
    "eletrônica", "eletronicos", "eletrônicos", "papelaria"
]


_VAREJO_MEDIO_NOISE_NAMES = [
    # Mercados municipais / Órgãos públicos
    "mercado municipal", "mercadão municipal", "mercadao municipal", "feira livre",
    # Usados / Brechós / Segunda mão / Antiguidades
    "usados", "usado", "segunda mão", "segunda mao", "brechó", "brecho", "móveis usados", "moveis usados", "eletros usados", "antiguidades", "bazar beneficente",
    # Saúde / Farmácias puras / Óticas / Clínicas
    "farmacia", "farmácia", "drogaria", "drogarias", "drogasil", "droga raia",
    "otica", "ótica", "optica", "óptica", "laboratorio", "laboratório",
    "clinica", "clínica", "hospital", "consultorio", "consultório", "odontologia", "dentista", "ortodontia",
    # Automotivo / Postos / Mecânica
    "auto pecas", "auto peças", "autopeças", "autopecas", "mecanica", "mecânica",
    "funilaria", "borracharia", "pneus", "posto de gasolina", "posto de combustivel", "lava rapido", "lava rápido", "centro automotivo",
    # Construção civil pesada
    "material de construcao", "material de construção", "tintas", "madeireira", "marmoraria", "vidracaria", "vidraçaria", "serralheria", "cimento", "areia",
    # Serviços administrativos e profissionais
    "imobiliaria", "imobiliária", "advocacia", "advogado", "contabilidade", "contabil", "despachante",
    # Estética / Beleza / Fitness
    "academia", "pilates", "crossfit", "barbearia", "salao de beleza", "salão de beleza", "estetica", "estética", "manicure",
    # Pets / Veterinária
    "pet shop", "veterinaria", "veterinária", "agropecuaria", "agropecuária",
    # Alimentação consumo imediato (Restaurantes/Bares/Padarias)
    "restaurante", "lanchonete", "pizzaria", "hamburgueria", "padaria", "confeitaria", "bar ", "churrascaria", "sorveteria",
]


_VAREJO_MEDIO_POSITIVE_TERMS = [
    "supermercado", "supermercados", "hipermercado", "hipermercados", "mercado", "mercados",
    "atacarejo", "atacarejos", "mercearia", "comercial de alimentos", "rede de supermercados",
    "moveis", "móveis", "eletro", "eletromoveis", "eletromóveis", "eletrodomesticos", "eletrodomésticos",
    "eletroportateis", "eletroportáteis", "departamento", "departamentos", "loja de departamentos",
    "utilidades", "utilidade", "variedades", "variedade", "bazar", "presentes", "artigos para o lar",
    "loja", "magazine", "comercio", "comércio", "comercial", "varejo", "varejista",
]


_MOBILIDADE_NOISE_NAMES = [
    # Eletropostos / Estações de Carga (não vendem veículos)
    "eletroposto",
    "estacao de recarga",
    "estação de recarga",
    "ponto de recarga",
    "posto de recarga",
    "chargestation",
    "ev charging",
    "carregador eletrico",
    "carregador elétrico",
    # Locação pública por app / Compartilhamento
    "bike itau",
    "bike sampa",
    "yellow bike",
    "grin",
    "ciclofaixa",
    "aluguel de bike",
    "aluguel de bicicleta",
    "locacao de patinete",
    "locação de patinete",
    # Oficinas mecânicas a combustão / Carros
    "troca de oleo",
    "troca de óleo",
    "funilaria",
    "pintura automotiva",
    "centro automotivo",
    "auto center",
    "mecanica automotiva",
    "mecânica automotiva",
    "retifica",
    "retífica",
    "oficina mecanica",
    "oficina mecânica",
    "alinhamento e balanceamento",
    "borracharia",
    "posto de combustivel",
    "posto de combustível",
    "conveniencia",
    "conveniência",
    # Auto Elétrica de carros a combustão (baterias/alternadores de automóveis)
    "auto eletrica",
    "auto elétrica",
    "eletrica automotiva",
    "elétrica automotiva",
    "auto eletrico",
    "auto elétrico",
    # Ortopedia / Cadeira de rodas motorizada
    "cadeira de rodas",
    "ortopedia",
    "ortopedica",
    "energia solar",
    "solar",
    "fotovoltaica",
    "fotovoltaico",
    "eletricista",
    "materiais eletricos",
    "material eletrico",
    "hidraulica",
    "vidros",
    "vidracaria",
    "multimarcas",
    "carros",
    "automoveis",
    "ortopédica",
]


_MOBILIDADE_POSITIVE_TERMS = [
    "moto eletrica", "moto elétrica", "motos eletricas", "motos elétricas",
    "bicicleta eletrica", "bicicleta elétrica", "bicicletas eletricas", "bicicletas elétricas",
    "bicicletaria eletrica", "bicicletaria elétrica", "bicicletaria e-bike", "bicicletaria ebike",
    "e-bike", "ebike", "scooter eletrica", "scooter elétrica", "scooters eletricas", "scooters elétricas",
    "patinete eletrico", "patinete elétrico", "patinetes eletricos", "patinetes elétricos",
    "veiculo eletrico", "veículo elétrico", "veiculos eletricos", "veículos elétricos",
    "mobilidade eletrica", "mobilidade elétrica", "mobilidade leve",
    "watts", "voltz", "shineray eletrica", "shineray elétrica", "niu", "super soco", "bee eletrica", "lev", "nxt", "muv", "two dogs",
    "concessionaria", "concessionária", "revenda de motos", "revenda de ebike", "revenda de bicicletas eletricas", "revenda de bicicletas elétricas",
]


_MOBILIDADE_B2B_HIGH_INTENT = [
    "distribuidor", "distribuidora", "atacadista", "atacado", "revenda", "importadora", "fornecedor", "concessionaria", "concessionária",
]


_MOBILIDADE_B2B_MEDIUM_INTENT = [
    "loja de motos eletricas", "loja de motos elétricas", "loja de bicicletas eletricas", "loja de bicicletas elétricas",
    "loja de e-bikes", "ebike shop", "loja de scooters", "veiculos eletricos", "veículos elétricos", "mobilidade eletrica", "mobilidade elétrica",
    "bicicletaria eletrica", "bicicletaria elétrica",
]


_MOBILIDADE_BUSINESS_HINTS = [
    "eletrica", "elétrica", "ebike", "e-bike", "scooter", "moto", "motos", "bike", "bikes",
    "bicicleta", "bicicletas", "mobilidade", "veiculos", "veículos", "motors", "ev",
    "distribuidora", "revenda", "loja", "concessionaria", "concessionária", "ltda", "me", "epp", "s.a",
]

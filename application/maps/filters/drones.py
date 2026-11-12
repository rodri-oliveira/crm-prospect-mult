from __future__ import annotations

from application.maps.text import _norm_key


_DRONE_POSITIVE_TERMS = [
    "drone", "dji", "fpv", "aeromodel", "radiocontrol", "rádio controle",
    "radio controle", "radiocontrol", "multirotor", "quadcopter",
    "parrot", "autel", "skydio", "hubsan", "syma",
    "aeromod", "planador", "helicóptero rc", "helicoptero rc",
]

_DRONE_NEGATIVE_CATEGORIES = [
    "photography studio", "estúdio fotográfico", "fotógrafo", "photographer",
    "sound equipment supplier", "áudio e vídeo", "audio e video",
    "sporting goods store", "artigos esportivos",
    "electronics store",   # sozinho é genérico demais; só bloqueado se sem positivo
    "security system supplier", "sistema de segurança", "cftv", "alarme",
    "musical instrument store", "instrumentos musicais",
    "rental service", "locadora",
    "video production", "produtora de vídeo",
]

_DRONE_NOISE_NAMES = [
    "aluguel", "alugação", "locação", "locação", "aluga drone",
    "piloto de drone", "serviço de drone", "filmagem", "filmagens", "fotografia aerea",
    "foto aerea", "aerial", "ceubô drone", "voo de drone",
    # Segurança / CFTV / Alarmes (não vendem drones)
    "cftv", "alarme", "alarmes", "segurança", "seguranca",
    "cerca eletrica", "cerca elétrica", "portão", "portao",
    "cabeamento estruturado", "intelbras", "câmera de segurança", "camera de seguranca",
    "monitoramento", "vigilância", "vigilancia",
    # Material elétrico / Utilidades / Auto peças (lixo genérico)
    "auto peças", "auto pecas", "autopeças", "autopecas",
    "material eletrico", "material elétrico", "eletromax",
    "utilidade", "utilidades", "presentes",
    "papelaria", "bazar",
    # Limpeza / Produtos não relacionados
    "limpeza", "produtos de limpeza", "distribuidora de limpeza",
    "distribuidora de produtos", "atacado",
    # Imagens / Serviços (não vendem drones)
    "imagens aereas", "imagem aerea", "imagens aéreas", "imagem aérea",
    "drone show", "drone light show",
    # Shows / Entretenimento
    "magic show", "espetaculo", "entretenimento",
]

def _filter_noise_drones(results: list[dict]) -> list[dict]:
    """Remove estabelecimentos que não têm relação com VENDA de drones.

    Lógica:
      - Remove nomes com termos de serviço puro (locação, filmagem)
      - Remove CFTV, alarmes, segurança, auto peças, material elétrico, limpeza
      - Verifica nome + categorias do Maps
      - Mantém apenas lojas/revendas de drones, aeromodelismo e FPV
    """
    filtered = []
    for item in results:
        nome = _norm_key(item.get("nome") or "")
        categorias_list = item.get("segmentos") or []
        categorias_str = " ".join([_norm_key(str(c)) for c in categorias_list])
        texto_para_busca = f"{nome} {categorias_str}"

        # Remove locadoras, prestadores de serviço e lojas irrelevantes
        is_noise = any(t in texto_para_busca for t in _DRONE_NOISE_NAMES)
        if is_noise:
            continue

        filtered.append(item)

    return filtered

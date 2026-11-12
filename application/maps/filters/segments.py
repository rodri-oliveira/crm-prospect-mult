from __future__ import annotations

from application.maps.filters.brinquedos import _filter_noise_brinquedos
from application.maps.filters.drones import _filter_noise_drones
from application.maps.filters.gamer import _filter_noise_gamer
from application.maps.filters.informatica import _filter_noise_informatica
from application.maps.filters.mobilidade import _filter_noise_mobilidade_eletrica
from application.maps.filters.sennheiser import _filter_noise_sennheiser
from application.maps.filters.varejo import _filter_noise_varejo_medio


def _filter_segment_noise(results: list[dict], seg: str) -> list[dict]:
    """Filtro semântico por segmento: descarta estabelecimentos que claramente
    não vendem os produtos do segmento alvo, mesmo que tenham aparecido na busca.
    """
    from application.maps.accessories import is_accessories, filter_accessories
    if is_accessories(seg):
        return filter_accessories(results)
    seg_clean = (seg or "").strip().lower()

    if "drone" in seg_clean:
        return _filter_noise_drones(results)

    if "inform" in seg_clean:
        return _filter_noise_informatica(results)

    if "sennheiser" in seg_clean:
        return _filter_noise_sennheiser(results)

    if "brinquedo" in seg_clean:
        return _filter_noise_brinquedos(results)

    if "gamer" in seg_clean:
        return _filter_noise_gamer(results)

    if "varej" in seg_clean:
        return _filter_noise_varejo_medio(results)

    if "mobilidade" in seg_clean:
        return _filter_noise_mobilidade_eletrica(results)

    return results

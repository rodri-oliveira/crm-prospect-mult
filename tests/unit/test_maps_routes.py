from interfaces.api.routes import _default_maps_estado


def test_default_maps_estado_does_not_guess_state_when_city_has_no_state():
    assert _default_maps_estado("Americana", "") == ""


def test_default_maps_estado_keeps_explicit_state_uppercase():
    assert _default_maps_estado("Niteroi", "rj") == "RJ"


def test_default_maps_estado_stays_empty_without_city():
    assert _default_maps_estado("", "") == ""

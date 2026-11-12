import pytest
from application.maps.accessories import accessories_queries, assess_accessories, filter_accessories, SEGMENT, safe_website
from application.maps.search_results import generate_queries_for_segments, SearchMapsResultsRequest, search_maps_results_with_repo
from domain.repositories.maps_existing_keys_repository import ExistingMapsKeys


@pytest.mark.parametrize('uf',['SP','RJ','MG','ES'])
def test_focus_has_small_local_queries_for_every_southeast_state(uf):
    result=generate_queries_for_segments([SEGMENT],'Cidade Teste',uf)
    assert result.primary_query.startswith('loja de informática em ')
    assert any(q['q'].startswith('suprimentos de informática em ') for q in result.queries)
    assert all(f'"Cidade Teste", {uf}' in q['q'] for q in result.queries)
    assert not any('Dell' in q['q'] or 'Lenovo' in q['q'] for q in result.queries)


@pytest.mark.parametrize('city,uf',[('','SP'),('Cidade',''),('Cidade','PR')])
def test_accessory_search_needs_explicit_southeast_location(city,uf):
    with pytest.raises(ValueError):accessories_queries(city,uf)


def test_query_is_not_evidence_and_phone_is_not_verified():
    item={'nome':'Loja Genérica','query_sources':['distribuidor de periféricos'], 'segmentos':[SEGMENT], 'telefone':'11999999999'}
    result=assess_accessories(item)
    assert not result['accessories_fit']
    assert not result['contact_verified']
    assert 'Confirmar venda de acessórios' in result['quality_notes']


def test_accessories_do_not_drop_small_resellers_or_turn_services_into_leads():
    items=[{'nome':'Loja de Informática','telefone':'2732221234'}, {'nome':'Consultoria de TI e Software'}, {'nome':'Loja a conferir'}]
    filtered=filter_accessories(items)
    assert [x['nome'] for x in filtered]==['Loja de Informática','Loja a conferir']
    assert items[0].get('quality_priority') is None


def test_focused_search_failure_is_not_success(monkeypatch):
    import services.maps_scrape_service as service
    monkeypatch.setattr(service,'scrape_maps_results',lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError('Blocked')))
    class EmptyRepo:
        def get_existing_maps_keys(self):return ExistingMapsKeys(set(),set(),{})
    result=search_maps_results_with_repo(SearchMapsResultsRequest('loja','Vitória','ES',[SEGMENT],20),EmptyRepo())
    assert not result.ok and result.modo=='error' and result.items==[]


@pytest.mark.parametrize('url',['javascript:alert(1)','data:text/html,<script>','https://user:pass@example.com','https://example.com/" onclick="x'])
def test_unsafe_website_rejected(url):
    assert not safe_website(url)

"""Synthetic merchant categories; no claim that candidates sell WATTS already."""
import pytest
from application.maps.car_dealers import SEGMENT, CAMPAIGN, car_dealer_queries, assess_car_dealer, filter_car_dealers, campaign_note
from application.maps.accessories import SEGMENT as ACCESSORIES, accessories_queries
from application.maps.search_results import generate_queries_for_segments, SearchMapsResultsRequest, search_maps_results_with_repo
from domain.repositories.maps_existing_keys_repository import ExistingMapsKeys


@pytest.mark.parametrize('city,uf',[('São Paulo','SP'),('Rio de Janeiro','RJ'),('Belo Horizonte','MG'),('Vitória','ES')])
def test_queries_seek_car_merchants_in_the_four_southeast_states(city,uf):
    result=generate_queries_for_segments([SEGMENT],city,uf)
    assert result.primary_query.startswith('loja de carros em ')
    assert all(f'"{city}", {uf}' in query['q'] for query in result.queries)
    assert any('seminovos' in query['q'] for query in result.queries)
    assert any('concessionária de automóveis' in query['q'] for query in result.queries)
    assert all('watts' not in query['q'].lower() and 'elétrica' not in query['q'].lower() for query in result.queries)


@pytest.mark.parametrize('uf',['PR','BA','','XX'])
def test_new_profile_requires_southeast_state(uf):
    with pytest.raises(ValueError):car_dealer_queries('Cidade',uf)


@pytest.mark.parametrize('name,category',[
    ('Exemplo Seminovos','Revendedora de carros usados'),
    ('Exemplo Automóveis','Loja de carros'),
    ('Marca Exemplo','Concessionária de automóveis'),
    ('Extra Veículos','Car dealer'),
    ('Oficina e Revenda de Automóveis Exemplo','Oficina mecânica'),
])
def test_accepts_car_sales_without_electric_vehicle_evidence(name,category):
    item={'nome':name,'categorias':[category]}
    result=filter_car_dealers([item])
    assert len(result)==1 and result[0]['campaign']==CAMPAIGN
    assert result[0]['contact_verified'] is False
    assert 'campaign' not in item


@pytest.mark.parametrize('name,category',[
    ('Oficina de Veículos Exemplo','Oficina mecânica'),
    ('Exemplo Autopeças','Loja de autopeças'),
    ('Locadora de Carros Exemplo','Locadora de veículos'),
    ('Estacionamento de Veículos Exemplo','Estacionamento'),
    ('Auto Escola Exemplo','Autoescola'),
    ('Exemplo Veículos','Concessionária de motos'),
    ('Loja de Veículos Exemplo','Loja de motocicletas'),
    ('Exemplo Veículos','Motorcycle dealer'),
    ('Exemplo Bicicletaria','Bicicletaria'),
])
def test_rejects_pure_services_and_other_vehicle_channels(name,category):
    assert not filter_car_dealers([{'nome':name,'categorias':[category],'segmentos':[SEGMENT],'query_sources':['loja de carros']}])


def test_search_terms_are_not_evidence_of_car_sales():
    assert not assess_car_dealer({'nome':'Empresa genérica','segmentos':[SEGMENT], 'query_sources':['revenda de veículos']})['profile_fit']


def test_default_accessories_queries_are_unchanged_and_mixed_search_contains_both():
    current=generate_queries_for_segments([ACCESSORIES],'Vitória','ES')
    assert current.queries==accessories_queries('Vitória','ES')
    combined=generate_queries_for_segments([ACCESSORIES,SEGMENT],'Vitória','ES')
    assert [q['segmento'] for q in combined.queries[:2]]==[ACCESSORIES,SEGMENT]
    assert {q['segmento'] for q in combined.queries}=={ACCESSORIES,SEGMENT}


class EmptyRepo:
    def get_existing_maps_keys(self):return ExistingMapsKeys(set(),set(),{})


def test_car_pipeline_bypasses_informatics_name_and_chain_exclusions(monkeypatch):
    import services.maps_scrape_service as service
    monkeypatch.setattr(service,'scrape_maps_results',lambda *a,**kw:[
        {'id':'car','nome':'Extra Veículos','categorias':['Car dealer']},
        {'id':'repair','nome':'Oficina de Veículos','categorias':['Oficina mecânica']},
        {'id':'wrongcity','nome':'Outra Automóveis','categorias':['Car dealer'],'cidade':'Curitiba','estado':'PR'},
    ])
    result=search_maps_results_with_repo(SearchMapsResultsRequest('loja de carros','Vitória','ES',[SEGMENT],200),EmptyRepo())
    assert result.ok and [item['id'] for item in result.items]==['car']
    assert result.items[0]['campaign']==CAMPAIGN


def test_mixed_search_does_not_stop_after_only_the_default_profile(monkeypatch):
    import services.maps_scrape_service as service
    def collect(query,**kwargs):
        if 'informática' in query:
            return [{'id':f'info{i}','nome':f'Loja Informática {i}','categorias':['Loja de informática']} for i in range(2)]
        return [{'id':f'car{i}','nome':f'Exemplo Automóveis {i}','categorias':['Car dealer']} for i in range(2)]
    monkeypatch.setattr(service,'scrape_maps_results',collect)
    result=search_maps_results_with_repo(SearchMapsResultsRequest('lojas','Vitória','ES',[ACCESSORIES,SEGMENT],2),EmptyRepo())
    assert result.ok and len(result.items)==2
    assert {query['segmento'] for query in result.query_stats}=={ACCESSORIES,SEGMENT}
    assert any(item.get('campaign')==CAMPAIGN for item in result.items)
    assert any(ACCESSORIES in item.get('segmentos',[]) for item in result.items)


def test_campaign_note_is_idempotent_and_does_not_change_accessories():
    note=campaign_note('Contato manual',SEGMENT)
    assert CAMPAIGN in note
    assert campaign_note(note,[SEGMENT])==note
    assert campaign_note('Contato manual',ACCESSORIES)=='Contato manual'


def test_collection_failure_is_not_presented_as_success_for_car_segment(monkeypatch):
    import services.maps_scrape_service as service
    def fail(*a,**kw):raise RuntimeError('collection unavailable')
    monkeypatch.setattr(service,'scrape_maps_results',fail)
    result=search_maps_results_with_repo(SearchMapsResultsRequest('loja de carros','Vitória','ES',[SEGMENT],20),EmptyRepo())
    assert not result.ok and result.modo=='error' and not result.items

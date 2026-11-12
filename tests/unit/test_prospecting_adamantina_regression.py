"""Cases reported by the user; source categories are fixtures, not live search results."""
import pytest
from application.maps.accessories import filter_accessories, filter_accessories_location, SEGMENT
from application.maps.search_results import SearchMapsResultsRequest, search_maps_results_with_repo
from domain.repositories.maps_existing_keys_repository import ExistingMapsKeys
from services.maps_card_parser import card_location, card_categories

SHOPS = ['Infotrônica', 'Mania Informática', 'BSN Tecnologia', 'Doctus Tecnologia',
         'Millenium Informática', 'Juday Cartuchos e Informática']


def candidates():
    stores = [{'id': str(i), 'nome': name, 'categorias':['Loja de informática'],
               'cidade':'Adamantina', 'estado':'SP'} for i,name in enumerate(SHOPS)]
    return stores + [
        {'id':'college','nome':'Fatec Adamantina - Faculdade de Tecnologia de Adamantina',
         'categorias':['Universidade pública'], '__raw_text':'Curso de informática e hardware'},
        {'id':'gates','nome':'F.A. Distribuidor Garen Adamantina - Portões eletrônicos e itens de segurança',
         'categorias':['Fornecedor de sistema de segurança']},
    ]


def test_keep_computer_stores_and_exclude_the_two_reported_false_positives():
    items=filter_accessories_location(filter_accessories(candidates()), 'Adamantina', 'SP')
    assert {row['nome'] for row in items} == set(SHOPS)


@pytest.mark.parametrize('name',['BSN Tecnologia','Doctus Tecnologia','Loja Exemplo - Assistência e vendas'])
def test_company_suffix_is_not_a_city(name):
    assert filter_accessories_location([{'nome':name}], 'Adamantina', 'SP')


@pytest.mark.parametrize('location',[{'cidade':'Suzano','estado':'SP'}, {'cidade':'Adamantina','estado':'RJ'},
                                     {'endereco':'Rua de teste, 10, Suzano - SP'}])
def test_explicit_other_location_is_rejected(location):
    assert not filter_accessories_location([{'nome':'Loja Informática',**location}],'Adamantina','SP')


def test_positive_search_segment_does_not_turn_a_college_into_a_retailer():
    assert filter_accessories([{'nome':'Fatec Adamantina','segmentos':[SEGMENT],
                               'query_sources':['loja de informática'], 'categorias':['Universidade pública']}]) == []


def test_card_parser_does_not_take_street_for_city():
    assert card_location('Loja Informática\nRua de teste, 10 - Centro, Adamantina - SP') == ('Adamantina','SP')
    assert card_location('Rua de teste, 10') == ('','')
    assert card_location('R. Paraná - SP') == ('','')
    assert card_categories('Infotrônica\n4,7 (20)\nLoja de informática · Rua de teste, 10', 'Infotrônica') == ['Loja de informática']


def test_qualification_counts_and_names_through_complete_search_pipeline(monkeypatch):
    import services.maps_scrape_service as service
    monkeypatch.setattr(service,'scrape_maps_results',lambda *a,**k: candidates())
    class EmptyRepo:
        def get_existing_maps_keys(self): return ExistingMapsKeys(set(),set(),{})
    response=search_maps_results_with_repo(SearchMapsResultsRequest('loja de informática','Adamantina','SP',[SEGMENT],200),EmptyRepo())
    assert response.ok
    assert {item['nome'] for item in response.items} == set(SHOPS)
    assert response.merged_after_dedupe == len(SHOPS)
    assert all(stat['collected']==8 and stat['after_activity']==6 and stat['after_location']==6 for stat in response.query_stats)
    assert response.query_stats[0]['new_unique']==6
    assert all(stat['new_unique']==0 for stat in response.query_stats[1:])


def test_card_text_does_not_include_neighboring_school():
    from services.maps_scrape_service import _result_card_text
    class Link:
        def __init__(self,href): self.href=href
        def get_attribute(self,_):return self.href
    class Links:
        def __init__(self,values):self.values=values
        def count(self):return len(self.values)
        def nth(self,index):return Link(self.values[index])
    class Parent:
        def __init__(self,text,links):self.text=text;self.links=links
        @property
        def first(self):return self
        def count(self):return 1
        def inner_text(self):return self.text
        def locator(self,_):return Links(self.links)
    href='/maps/place/Infotronica'
    class Anchor(Link):
        def locator(self,selector):
            depth=int(selector.split('[')[-1][:-1])
            return Parent('Infotrônica\nLoja de informática' if depth==1 else 'Infotrônica\nFatec\nUniversidade pública',
                          [href] if depth==1 else [href,'/maps/place/Fatec'])
    assert _result_card_text(Anchor(href)) == 'Infotrônica\nLoja de informática'

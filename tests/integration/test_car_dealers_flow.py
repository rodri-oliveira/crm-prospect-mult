import html
from io import BytesIO
import re
import pytest
import database
from application.maps.car_dealers import SEGMENT, CAMPAIGN
from application.prospeccao.import_csv import preview_csv
from .conftest import csrf


def test_new_segment_available_in_search_and_registration(browser):
    assert f'value="{SEGMENT}"' in browser.get('/prospeccao').get_data(as_text=True)
    assert f'value="{SEGMENT}"' in browser.get('/leads').get_data(as_text=True)
    result=browser.get('/api/maps/queries',query_string={'cidade':'Vitória','estado':'ES','segmentos':SEGMENT})
    assert result.status_code==200 and result.get_json()['primary_query'].startswith('loja de carros')


def test_manual_dealer_remains_prospect_and_campaign_survives_conversion(browser):
    result=browser.post('/api/prospeccao/rascunho/novo',json={'nome_loja':'Exemplo Automóveis','cidade':'Vitória','estado':'ES','segmento':SEGMENT},headers={'X-CSRF-Token':csrf(browser)})
    assert result.status_code==200
    pid=result.get_json()['id']
    with database.get_db_connection() as conn:
        row=conn.execute('SELECT * FROM prospeccao_temp WHERE id=?',(pid,)).fetchone()
        assert row['segmento']==SEGMENT and row['status_prospeccao']=='Não contatado'
        assert CAMPAIGN in row['observacao']
    result=browser.post(f'/prospeccao/rascunho/{pid}/status',data={'status':'Em negociação','csrf_token':csrf(browser)})
    assert result.status_code==302
    with database.get_db_connection() as conn:
        row=conn.execute('SELECT * FROM leads').fetchone()
        assert CAMPAIGN in row['observacoes'] and row['status']=='Em negociação'
        assert conn.execute('SELECT segmento FROM segmentos_loja WHERE lead_id=?',(row['id'],)).fetchone()[0]==SEGMENT


def test_maps_selection_preserves_dealer_profile_and_campaign(browser):
    result=browser.post('/api/maps/adicionar',json={'items':[{'id':'synthetic-dealer','nome':'Exemplo Seminovos','cidade':'Vitória','estado':'ES','segmentos':[SEGMENT]}]},headers={'X-CSRF-Token':csrf(browser)})
    assert result.status_code==200 and result.get_json()['added_count']==1
    with database.get_db_connection() as conn:
        row=conn.execute('SELECT * FROM prospeccao_temp').fetchone()
        assert row['segmento']==SEGMENT and CAMPAIGN in row['observacao']


def test_car_csv_preview_signed_confirmation_and_profile_persistence(browser):
    raw=b'nome_loja;cidade;estado;telefone\nExemplo Automoveis;Vitoria;ES;2732221234\n'
    result=browser.post('/prospeccao/importar',data={'file':(BytesIO(raw),'cars.csv'),'segmento':SEGMENT,'csrf_token':csrf(browser)})
    assert result.status_code==200 and CAMPAIGN in result.get_data(as_text=True)
    token=html.unescape(re.search(r'name="preview_token" value="([^"]+)"',result.get_data(as_text=True)).group(1))
    # The signed preview, not a different confirmation field, determines the imported profile.
    result=browser.post('/prospeccao/importar',data={'action':'confirm','preview_token':token,'selected':'0','segmento':'Acessórios de informática','csrf_token':csrf(browser)})
    assert result.status_code==200
    with database.get_db_connection() as conn:
        row=conn.execute('SELECT * FROM prospeccao_temp').fetchone()
        assert row['segmento']==SEGMENT and CAMPAIGN in row['observacao']
        assert row['status_prospeccao']=='Não contatado'


def test_unknown_import_profile_rejected():
    with pytest.raises(ValueError):preview_csv(b'anything',segmento='unknown')

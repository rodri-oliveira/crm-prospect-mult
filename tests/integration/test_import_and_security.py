from io import BytesIO
import pytest
import database
from application.prospeccao.import_csv import preview_csv
from infrastructure.repositories.csv_prospect_repository import CsvProspectRepository
from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository
from .conftest import csrf


def content(rows):
    return ('nome_loja;cidade;estado;telefone;site\n'+rows).encode('utf-8-sig')


def test_csv_preview_confirm_and_reimport(crm,browser):
    raw=content('Loja Sintética Informática;Vitória;ES;2732221234;example.com\n')
    response=browser.post('/prospeccao/importar',data={'file':(BytesIO(raw),'lojas.csv'),'csrf_token':csrf(browser)})
    assert response.status_code==200
    import re, html
    token=html.unescape(re.search(r'name="preview_token" value="([^"]+)"', response.get_data(as_text=True)).group(1))
    for expected in ['1 contatos importados','0 contatos importados']:
        response=browser.post('/prospeccao/importar',data={'action':'confirm','preview_token':token,'selected':'0','csrf_token':csrf(browser)})
        assert response.status_code==200
        assert expected in response.get_data(as_text=True)
    with database.get_db_connection() as conn:
        row=conn.execute('SELECT * FROM prospeccao_temp').fetchone()
        assert row['status_prospeccao']=='Não contatado'
        assert 'example.com' in row['site']
        assert 'Revisão pendente' in row['observacao']
        assert conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]==0


def test_import_detects_archived_duplicates_and_preserves_notes(crm):
    repo=SqliteProspeccaoRepository()
    pid,_=repo.add({'nome_loja':'Loja Sintética Informática','cidade':'Vitória','estado':'ES','observacoes':'Histórico importante'})
    repo.arquivar(pid)
    rows=preview_csv(content('LOJA SINTETICA INFORMATICA;Vitoria;es;2732221234;\n'))
    assert CsvProspectRepository().import_rows([r['data'] for r in rows])=={'added':0,'duplicates':1}
    assert repo.get_by_id(pid)['observacao']=='Histórico importante'
    assert repo.get_by_id(pid)['arquivado']==1


@pytest.mark.parametrize('rows,expected',[
    ('Loja;Curitiba;PR;4132221234;\n','UF fora do Sudeste'),
    ('Loja;Vitória;ES;123;\n','DDD'),
    ('Loja;Vitória;ES;;\n','canal de contato'),
    ('Loja;Vitória;ES;;javascript:alert(1)\n','URL inválida'),
])
def test_bad_csv_lines_are_not_importable(rows,expected):
    result=preview_csv(content(rows))
    assert expected in ';'.join(result[0]['errors'])


def test_import_invalid_signature_and_missing_selection(crm,browser):
    r=browser.post('/prospeccao/importar',data={'action':'confirm','preview_token':'forged','csrf_token':csrf(browser)})
    assert r.status_code==400
    with database.get_db_connection() as conn:
        assert conn.execute('SELECT COUNT(*) FROM prospeccao_temp').fetchone()[0]==0


def test_csrf_and_local_access_controls(crm,browser):
    assert browser.post('/api/prospeccao/rascunho/novo',json={'nome_loja':'forged'}).status_code==400
    assert browser.get('/leads',environ_overrides={'REMOTE_ADDR':'192.0.2.10'}).status_code==403
    assert browser.get('/leads',base_url='http://untrusted.example').status_code==403
    assert browser.get('/leads').headers['X-Content-Type-Options']=='nosniff'


def test_configured_auth_required_for_reads_and_writes(crm,monkeypatch):
    app,_=crm
    monkeypatch.setitem(app.config,'CRM_USERNAME','test')
    monkeypatch.setitem(app.config,'CRM_PASSWORD','test-password')
    client=app.test_client()
    assert client.get('/leads').status_code==401
    assert client.post('/api/prospeccao/rascunho/novo',json={}).status_code==401
    assert client.get('/leads',auth=('test','wrong')).status_code==401
    assert client.get('/leads',auth=('test','test-password')).status_code==200


def test_backup_is_readable_and_does_not_overwrite(crm,tmp_path):
    from scripts.backup_database import backup_database
    app,path=crm
    SqliteProspeccaoRepository().add({'nome_loja':'Backup test'})
    output=tmp_path/'copy.db'
    backup_database(path,output)
    with database.get_db_connection(str(output)) as conn:
        assert conn.execute('SELECT COUNT(*) FROM prospeccao_temp').fetchone()[0]==1
    with pytest.raises(ValueError):backup_database(path,output)

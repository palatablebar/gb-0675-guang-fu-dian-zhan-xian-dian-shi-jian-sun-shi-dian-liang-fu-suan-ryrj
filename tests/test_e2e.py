from fastapi.testclient import TestClient
from app import main,store
from app.engine import evaluate
import pytest

def client(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB_PATH',str(tmp_path/'test.sqlite'));return TestClient(main.app)
def test_api_idempotent(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);a=c.post('/api/runs',json={}).json();b=c.post('/api/runs',json={}).json();assert a['manifest']['run_id']==b['manifest']['run_id'];assert len(c.get('/api/runs').json())==1
def test_stale_review(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);a=c.post('/api/runs',json={}).json();url='/api/runs/'+a['manifest']['run_id']+'/review';assert c.post(url,json={'revision':1}).status_code==200;assert c.post(url,json={'revision':1}).status_code==409
def test_seven_entries(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch)
    for k in main.MODULES:
        assert c.post('/api/'+k,json={}).status_code==200
        assert c.get('/'+k).status_code==200
def test_bad_dataset(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);assert c.post('/api/runs',json={'dataset':'../bad'}).status_code==422
def test_missing_run(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);assert c.get('/api/runs/none').status_code==404
def test_restart_store(tmp_path,sample):
    p=str(tmp_path/'durable.sqlite');store.save(p,sample);assert store.get(p,sample['manifest']['run_id'])['manifest']['sha256']==sample['manifest']['sha256']
def test_bad_revision(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch);s=c.post('/api/runs',json={}).json();assert c.post('/api/runs/'+s['manifest']['run_id']+'/review',json={'revision':0}).status_code==422

def test_clean_navigation_run_preserved(tmp_path,monkeypatch):
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={'dataset':'clean'}).json()
    rid=run['manifest']['run_id']
    for k in main.MODULES:
        html=c.get('/'+k+'?run_id='+rid).text
        assert '?run_id='+rid in html
        assert rid in html
    assert c.get('/api/export/'+rid).status_code==200

def test_custom_csv_snapshot_and_navigation(tmp_path,monkeypatch):
    from app.config import ROOT
    c=client(tmp_path,monkeypatch)
    original=(ROOT/'sample_data/clean.csv').read_text()
    # 改成独立于所有仓内样例的证据编号，追踪其跨页与重跑行为。
    first=original.splitlines()[1].split(',')[0]
    custom=original.replace(first,first+'-CUSTOM')
    result=c.post('/api/runs',json={'csv_text':custom}).json()
    rid=result['manifest']['run_id']
    assert '-CUSTOM' in str(result['records']) or '-CUSTOM' in str(result['quarantine'])
    for key in main.MODULES:
        response=c.get('/'+key+'?run_id='+rid)
        assert response.status_code==200
        assert '?run_id='+rid in response.text
    repeated=c.post('/api/runs/'+rid+'/rerun',json={})
    assert repeated.status_code==200
    assert repeated.json()['manifest']['run_id']==rid
    assert repeated.json()['manifest']['sha256']==result['manifest']['sha256']

def test_failed_recalc_keeps_old_version(tmp_path,monkeypatch):
    # 补正或重算失败时保留旧版，不新增批次、不丢记录
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={'dataset':'clean'}).json();rid=run['manifest']['run_id']
    assert c.post('/api/runs',json={'csv_text':'not,a,valid,header'}).status_code==422
    assert c.post('/api/runs/'+rid+'/rerun',json={}).status_code==200
    history=c.get('/api/runs').json();assert len(history)==1 and history[0]['id']==rid
    kept=c.get('/api/runs/'+rid).json()
    assert kept['manifest']['sha256']==run['manifest']['sha256']
    assert kept['balance']['loss_kwh']=='36.6667'

def test_retry_same_basis_no_new_batch(tmp_path,monkeypatch):
    # 重试同一依据不新增批次，复核状态随旧版保留
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={'dataset':'clean'}).json();rid=run['manifest']['run_id']
    url='/api/runs/'+rid+'/review';assert c.post(url,json={'revision':1}).status_code==200
    again=c.post('/api/runs',json={'dataset':'clean'}).json()
    assert again['manifest']['run_id']==rid
    assert len(c.get('/api/runs').json())==1
    kept=c.get('/api/runs/'+rid).json();assert kept['status']=='已复核' and kept['revision']==2

def test_region_report_shows_station_attribution(tmp_path,monkeypatch):
    # 页面显示场站归属、可结算损失与待查片段
    c=client(tmp_path,monkeypatch)
    run=c.post('/api/runs',json={}).json();rid=run['manifest']['run_id']
    html=c.get('/reconcile?run_id='+rid).text
    assert '北岭' in html and '南岭' in html and '区域合计' in html
    assert '可结算损失' in html and '待查片段' in html
    body=c.get('/api/runs/'+rid).json()
    assert body['balance']['region_balanced'] is True
    assert sum(1 for q in body['quarantine'] if q['code'] in ('MISSING_STATION','UNKNOWN_STATION'))==3

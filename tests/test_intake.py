from app.engine import evaluate
from app.errors import BusinessError
from app.config import ROOT
import pytest

def test_bom_source(sample):
    # TRAP-02
    assert sample['records'][0]['id']=='INV-A-00'
def test_legacy_source():
    # TRAP-01
    s=evaluate({'dataset':'legacy'});assert s['encoding']=='gb18030';assert s['records'][0]['status']=='健康'
def test_segment_header(sample):
    # TRAP-04
    assert sample['counts']['repeated_header']==1
def test_bad_column(sample):
    # TRAP-05
    assert next(r for r in sample['quarantine'] if r['id']=='COLUMN')['code']=='COLUMN_COUNT'
def test_same_source_duplicate(sample):
    assert sample['counts']['duplicate']==1
def test_three_empty_types():
    # TRAP-18
    for text,code in [('', 'EMPTY_FILE'),('\n\n','BLANK_FILE'),((ROOT/'sample_data/clean.csv').read_text().splitlines()[0]+'\n','HEADER_ONLY')]:
        with pytest.raises(BusinessError) as e:evaluate({'csv_text':text})
        assert e.value.code==code
def test_source_rows_real(clean):
    assert clean['counts']['input']==49

def test_same_name_cross_station_no_merge(clean):
    # TRAP-24 两站同名 INV-A 与 E-01 各自独立落站，不按原编号合并
    e01=[r for r in clean['records'] if r['id']=='E-01']
    assert sorted(r['station'] for r in e01)==['北岭','南岭']
    assert {r['uid'] for r in clean['records'] if r['device']=='INV-A'}=={'北岭/INV-A','南岭/INV-A'}
    assert not any(q['code']=='DUPLICATE_CONFLICT' for q in clean['quarantine'])

def test_same_record_id_two_stations(clean):
    # 同一证据号在两站同时出现时各自采信，不算重复
    from app.config import ROOT
    text=(ROOT/'sample_data/clean.csv').read_text()
    first_nan=text.split('NAN-A-00')[0]
    custom=text.replace('NAN-A-00','INV-A-00')
    s=evaluate({'csv_text':custom})
    assert s['counts']['duplicate']==0
    assert sum(1 for r in s['records'] if r['id']=='INV-A-00')==2

def test_missing_station_pending(sample):
    # TRAP-25 缺少场站依据的记录隔离待查，不落任何场站
    orphans={r['id']:r for r in sample['quarantine'] if r['id'].startswith('ORPHAN')}
    assert orphans['ORPHAN-1']['code']=='MISSING_STATION'
    assert orphans['ORPHAN-2']['code']=='MISSING_STATION'
    assert orphans['ORPHAN-3']['code']=='UNKNOWN_STATION'
    assert orphans['ORPHAN-2']['raw']['kind']=='EVENT'
    assert not any(r['id'].startswith('ORPHAN') for r in sample['records'])

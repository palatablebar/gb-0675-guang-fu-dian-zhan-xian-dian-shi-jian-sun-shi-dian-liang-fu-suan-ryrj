from app.modules.baseline.rules import estimate
from copy import deepcopy

def test_reference_baseline_real(clean):
    assert clean['estimates'][0]['baseline_kw']=='100'
def test_no_reference_not_zero(sample):
    row=next(r for r in sample['estimates'] if r['code']=='NO_REFERENCE');assert row['baseline_kw'] is None;assert row['reference_ids']==['北岭/REF-A1-10']
def test_target_gap_real(sample):
    assert next(r for r in sample['estimates'] if r['code']=='TARGET_GAP')['baseline_kw'] is None
def test_other_irradiance_bin_ignored(clean):
    rows=[dict(r) for r in clean['records']]
    for row in rows:
        if row['id']=='REF-A1-00' and row['station']=='北岭':row['irradiance']='700'
    assert estimate(clean['segments'][0],rows,clean['context'])['code']=='NO_REFERENCE'
def test_wrong_zone_ignored(clean):
    c=deepcopy(clean['context']);c['devices']['北岭/REF-A2']['zone']='西区';assert estimate(clean['segments'][0],clean['records'],c)['code']=='NO_REFERENCE'
def test_curtailed_reference_ignored(clean):
    rows=clean['records']+[dict(next(r for r in clean['records'] if r['id']=='E-01' and r['station']=='北岭'),id='REF-CURTAIL',device='REF-A2',uid='北岭/REF-A2')];assert estimate(clean['segments'][0],rows,clean['context'])['code']=='NO_REFERENCE'
def test_capacity_normalization(clean):
    c=deepcopy(clean['context']);c['devices']['北岭/REF-A1']['capacity_kw']='200';result=estimate(clean['segments'][0],clean['records'],c);assert result['baseline_kw']=='75.00'

def test_cross_station_reference_ignored(clean):
    # 南岭同区域同时刻对照不为北岭所用，缺本站对照保持未定
    rows=[r for r in clean['records'] if not (r['station']=='北岭' and r['device'].startswith('REF-A') and r['at']=='2026-10-15T02:00:00+00:00')]
    result=estimate(clean['segments'][0],rows,clean['context'])
    assert result['code']=='NO_REFERENCE';assert result['baseline_kw'] is None
def test_reference_ids_station_qualified(clean):
    south=next(r for r in clean['estimates'] if r['uid']=='南岭/INV-A')
    assert south['code']=='ESTIMATED';assert all(x.startswith('南岭/') for x in south['reference_ids'])

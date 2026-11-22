from app.modules.devices.rules import normalize
from app.errors import BusinessError
import pytest

def test_units_real(clean):
    assert clean['records'][0]['power_kw']=='60'
def test_sentinel_real(sample):
    # TRAP-07
    assert next(r for r in sample['quarantine'] if r['id']=='BAD1')['code']=='MISSING_VALUE'
def test_conflict_both_isolated(sample):
    # TRAP-14
    assert len([r for r in sample['quarantine'] if r['code']=='SAMPLE_CONFLICT'])==2;assert not any(r['id']=='INV-A-20' and r['station']=='北岭' for r in sample['records'])
def test_megawatt_conversion(clean):
    # TRAP-15
    row=normalize(dict(clean['records'][0],power='0.06',unit='MW'),clean['context']);assert row['power_kw']=='60.00'
def test_fullwidth_number(clean):
    # TRAP-06
    row=normalize(dict(clean['records'][0],irradiance='１,０００'),clean['context']);assert row['irradiance']=='1000'
def test_unknown_device(clean):
    with pytest.raises(BusinessError):normalize(dict(clean['records'][0],device='NONE'),clean['context'])
def test_time_equivalence(clean):
    # TRAP-11
    row=normalize(dict(clean['records'][0],at='2026-10-15T02:00:00Z'),clean['context']);assert row['at']==clean['records'][0]['at']

def test_uid_station_namespaced(clean):
    # 同名设备按场站命名空间区分
    row=normalize(dict(clean['records'][0]),clean['context']);assert row['uid']=='北岭/INV-A'
def test_missing_station_raises(clean):
    with pytest.raises(BusinessError) as e:normalize(dict(clean['records'][0],station=''),clean['context'])
    assert e.value.code=='MISSING_STATION'
def test_unknown_station_raises(clean):
    with pytest.raises(BusinessError) as e:normalize(dict(clean['records'][0],station='西岭'),clean['context'])
    assert e.value.code=='UNKNOWN_STATION'
def test_cross_station_conflict_not_implicated(clean):
    # 北岭冲突隔离不连坐南岭同刻同名设备
    from app.engine import evaluate
    s=evaluate({'dataset':'dirty'})
    assert any(r['uid']=='南岭/INV-A' and r['at']=='2026-10-15T02:20:00+00:00' for r in s['records'])

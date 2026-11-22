from app.modules.reconcile.rules import reconcile
from copy import deepcopy
from decimal import Decimal

def test_input_rows_real(sample):
    assert sample['balance']['input']==59;assert sample['balance']['accepted']==48;assert sample['balance']['quarantined']==8;assert sample['balance']['row_balanced']
def test_clean_energy_real(clean):
    assert clean['balance']['loss_kwh']=='36.6667';assert clean['balance']['actual_kwh']=='80.0000';assert clean['balance']['energy_balanced']
def test_unknown_time_real(sample):
    assert sample['balance']['unknown_seconds']==1200;assert sample['balance']['unknown_segments']==2
def test_union_time_conservation(clean):
    assert clean['balance']['union_seconds']==clean['balance']['slice_seconds']==4800
def test_time_tamper(clean):
    s=deepcopy(clean);s['energy_rows'][0]['seconds']+=1;assert reconcile(s)['time_balanced'] is False
def test_energy_tamper(clean):
    s=deepcopy(clean);s['energy_rows'][0]['loss_kwh']='999';assert reconcile(s)['energy_balanced'] is False
def test_record_tamper(sample):
    s=deepcopy(sample);s['records'].pop();assert reconcile(s)['row_balanced'] is False

def test_region_equals_station_sum(clean):
    # 区域合计必须等于各站结果之和
    b=clean['balance'];stations={s['station']:s for s in b['stations']}
    assert stations['北岭']['loss_kwh']=='26.6667';assert stations['南岭']['loss_kwh']=='10.0000'
    assert Decimal(b['loss_kwh'])==sum(Decimal(s['loss_kwh']) for s in b['stations'])
    assert Decimal(b['actual_kwh'])==sum(Decimal(s['actual_kwh']) for s in b['stations'])
    assert b['union_seconds']==sum(s['union_seconds'] for s in b['stations'])
    assert b['region_balanced'] is True
def test_station_internal_balance(clean):
    # 场站内事件并集=切片、基线=实际+损失，各自对平
    for s in clean['balance']['stations']:
        assert s['time_balanced'] and s['energy_balanced']
def test_station_tamper_breaks_region(clean):
    # 把一行改到未登记场站：站级合计与全批口径相抵，区域不可加总
    s=deepcopy(clean);s['energy_rows'][0]['station']='西岭';assert reconcile(s)['region_balanced'] is False
def test_union_station_tamper_breaks_region(clean):
    s=deepcopy(clean);s['event_unions'][0]['station']='西岭';assert reconcile(s)['region_balanced'] is False
def test_dirty_station_pending_isolated(sample):
    # 缺场站行不进任何场站结果，只进待查
    stations={s['station']:s for s in sample['balance']['stations']}
    assert stations['北岭']['unknown_segments']==2;assert stations['南岭']['unknown_segments']==0
    assert stations['南岭']['loss_kwh']=='10.0000';assert sample['balance']['region_balanced'] is True

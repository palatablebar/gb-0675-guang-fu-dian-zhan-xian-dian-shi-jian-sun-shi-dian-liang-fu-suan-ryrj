from app.modules.slicing.rules import union_events,slice_intervals
from app.coerce import instant

def test_overlapping_real(clean):
    # TRAP-23
    a=next(r for r in clean['event_unions'] if r['uid']=='北岭/INV-A');assert a['seconds']==1800;assert a['event_ids']==['北岭/E-01','北岭/E-02']
def test_union_not_double_count(clean):
    assert sum(r['seconds'] for r in clean['segments'] if r['uid']=='北岭/INV-A')==1800
def test_missing_target_real(sample):
    assert any(r['actual_kw'] is None for r in sample['segments'])
def test_adjacent_events_merge(clean):
    e=[r for r in clean['records'] if r['id']=='E-01' and r['station']=='北岭'][0];other=dict(e,id='E-09',start=e['end'],end='2026-10-15T02:30:00+00:00');u=union_events([other,e]);assert len(u)==1;assert (u[0]['end']-u[0]['start']).total_seconds()==1800
def test_nonoverlap_remains_separate(clean):
    e=[r for r in clean['records'] if r['id']=='E-01' and r['station']=='北岭'][0];other=dict(e,id='E-09',start='2026-10-15T03:00:00+00:00',end='2026-10-15T03:10:00+00:00');assert len(union_events([e,other]))==2
def test_order_invariant_slice(clean):
    a=slice_intervals(clean['records'],clean['context']);b=slice_intervals(list(reversed(clean['records'])),clean['context']);assert a==b
def test_split_boundary_inside_sample(clean):
    rows=[dict(r) for r in clean['records'] if r['kind']!='EVENT'];rows.append(dict(next(r for r in clean['records'] if r['id']=='E-01' and r['station']=='北岭'),start='2026-10-15T02:05:00+00:00',end='2026-10-15T02:15:00+00:00'));segments,_=slice_intervals(rows,clean['context']);assert [r['seconds'] for r in segments]==[300,300]

def test_same_event_id_two_unions(clean):
    # 两站同名 E-01 形成各自并集，事件依据带场站
    unions={u['uid']:u for u in clean['event_unions']}
    assert unions['南岭/INV-A']['event_ids']==['南岭/E-01']
    assert unions['南岭/INV-A']['seconds']==1800
    assert unions['北岭/INV-A']['event_ids']==['北岭/E-01','北岭/E-02']
def test_segment_carries_station(clean):
    assert {r['station'] for r in clean['segments']}=={'北岭','南岭'}
    assert all(r['sample_id'].startswith(r['station']+'/') for r in clean['segments'] if r['sample_id'])

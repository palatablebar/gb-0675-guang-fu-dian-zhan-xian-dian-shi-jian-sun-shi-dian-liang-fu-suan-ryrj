from decimal import Decimal
from app.coerce import number

ENERGY_KEYS=['loss_kwh','actual_kwh','baseline_kwh']

def _sum(rows,key):
    return sum((number(r[key]) for r in rows),Decimal(0))

def reconcile(state):
    # Decimal周期小数允许最后一位精度误差，展示前统一量化到0.0001kWh再检查。
    quant=lambda v:v.quantize(Decimal('.0001'))
    rows_all=state['energy_rows'];unions_all=state['event_unions']
    station_rows=[];station_raw=[]
    for station in state['context']['stations']:
        rows=[r for r in rows_all if r['station']==station];unions=[u for u in unions_all if u['station']==station]
        known=[r for r in rows if r['loss_kwh'] is not None];unknown=[r for r in rows if r['loss_kwh'] is None]
        sums={k:_sum(known,k) for k in ENERGY_KEYS}
        union_seconds=sum(u['seconds'] for u in unions);slice_seconds=sum(r['seconds'] for r in rows)
        station_raw.append(sums)
        station_rows.append({'station':station,'union_seconds':union_seconds,'slice_seconds':slice_seconds,'time_balanced':union_seconds==slice_seconds,'loss_kwh':str(quant(sums['loss_kwh'])),'actual_kwh':str(quant(sums['actual_kwh'])),'baseline_kwh':str(quant(sums['baseline_kwh'])),'energy_balanced':quant(sums['baseline_kwh'])==quant(sums['actual_kwh']+sums['loss_kwh']),'unknown_segments':len(unknown),'unknown_seconds':sum(r['seconds'] for r in unknown)})
    # 区域合计=各站结果之和；另按全批直接合计核验，未归集到登记场站的行会让两口径相抵，防止漏记与串站。
    regional={k:sum((s[k] for s in station_raw),Decimal(0)) for k in ENERGY_KEYS}
    known_all=[r for r in rows_all if r['loss_kwh'] is not None];unknown_all=[r for r in rows_all if r['loss_kwh'] is None]
    direct={k:_sum(known_all,k) for k in ENERGY_KEYS}
    union_seconds=sum(u['seconds'] for u in unions_all);slice_seconds=sum(r['seconds'] for r in rows_all);unknown_seconds=sum(r['seconds'] for r in unknown_all)
    region_balanced=all(quant(regional[k])==quant(direct[k]) for k in ENERGY_KEYS) and sum(u['seconds'] for u in unions_all if u['station'] in state['context']['stations'])==union_seconds and sum(r['seconds'] for r in unknown_all if r['station'] in state['context']['stations'])==unknown_seconds
    c=state['counts'];explained=len(state['records'])+len(state['quarantine'])+c['blank']+c['duplicate']+c['repeated_header']
    return {'input':c['input'],'accepted':len(state['records']),'quarantined':len(state['quarantine']),'row_balanced':explained==c['input'],'union_seconds':union_seconds,'slice_seconds':slice_seconds,'time_balanced':union_seconds==slice_seconds and all(s['time_balanced'] for s in station_rows),'loss_kwh':str(quant(regional['loss_kwh'])),'actual_kwh':str(quant(regional['actual_kwh'])),'baseline_kwh':str(quant(regional['baseline_kwh'])),'energy_balanced':quant(regional['baseline_kwh'])==quant(regional['actual_kwh']+regional['loss_kwh']) and all(s['energy_balanced'] for s in station_rows),'unknown_segments':len(unknown_all),'unknown_seconds':unknown_seconds,'stations':station_rows,'region_balanced':region_balanced}
def apply(state):
    state['balance']=reconcile(state);b=state['balance']
    rows=b['stations']+[{'station':'区域合计','union_seconds':b['union_seconds'],'slice_seconds':b['slice_seconds'],'time_balanced':b['time_balanced'],'loss_kwh':b['loss_kwh'],'actual_kwh':b['actual_kwh'],'baseline_kwh':b['baseline_kwh'],'energy_balanced':b['energy_balanced'],'unknown_segments':b['unknown_segments'],'unknown_seconds':b['unknown_seconds']}]
    state['views']['reconcile']={'title':'场站对平与区域合计','rows':rows,'metrics':{'可结算损失_kWh':b['loss_kwh'],'待查片段':b['unknown_segments']+b['quarantined'],'区域可加总':'是' if b['region_balanced'] else '否'}}

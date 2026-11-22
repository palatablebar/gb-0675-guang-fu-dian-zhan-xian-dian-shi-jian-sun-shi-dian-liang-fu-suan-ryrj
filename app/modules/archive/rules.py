import hashlib,json

def archive_decision(state):
    b=state['balance'];pending=b['unknown_segments']+len(state['quarantine'])
    ready=b['row_balanced'] and b['time_balanced'] and b['energy_balanced'] and b['region_balanced'] and not pending
    return {'status':'可归档' if ready else '待复核','seal':hashlib.sha256(json.dumps(state['energy_rows'],sort_keys=True).encode()).hexdigest(),'segments':len(state['energy_rows']),'unknown':b['unknown_segments'],'pending':pending}
def apply(state):
    state['archive']=archive_decision(state);state['views']['archive']={'title':'运行凭证','rows':state['event_unions'],'metrics':{'切片':state['archive']['segments'],'待查片段':state['archive']['pending'],'状态':state['archive']['status']}}

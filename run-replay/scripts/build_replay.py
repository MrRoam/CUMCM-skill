"""Validate a single-run replay and embed it in the bundled HTML fragment."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path

Q3 = dict(domain_radius=1800, coverage_radius=1000, clear_radius=20,
          bearing_length=1500, angle_error_deg=1.005, unit='米', agent_label='机器狗')


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('Non-finite number in replay')
    if isinstance(value, dict):
        for x in value.values(): finite(x)
    elif isinstance(value, list):
        for x in value: finite(x)


def point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or not all(
            isinstance(v, (int, float)) and math.isfinite(v) for v in value):
        raise ValueError('Invalid 2D coordinate')


def validate(data):
    finite(data)
    frames, actions = data['frames'], data['actions']
    n = len(actions)
    if len(frames) != n + 1 or len(data['single']) != n:
        raise ValueError('N actions require N+1 frames and N single-step explanations')
    previous = -math.inf
    ids = None
    for f in frames:
        point(f['q'])
        if f['time'] < previous or f['time'] < 0:
            raise ValueError('Time must be nonnegative and monotone')
        previous = f['time']
        current = [c['j'] for c in f['channels']]
        if len(current) != len(set(current)) or any(not isinstance(j,int) or j<=0 for j in current):
            raise ValueError('Channel IDs must be unique positive integers')
        if ids is not None and set(current) != ids: raise ValueError('Channel list changed between frames')
        ids = set(current)
        for c in f['channels']:
            if c['status'] not in ('unknown','found','cleared','absent'): raise ValueError('Invalid status')
            if 'center' in c: point(c['center'])
            for q in c.get('polygon',[]): point(q)
            if c.get('radius',0)<0: raise ValueError('Negative radius')
        if not set(f['seen']).issubset(ids): raise ValueError('Unknown ID in seen')
    for i, a in enumerate(actions, 1):
        point(a['position'])
        if a['channel'] not in ids: raise ValueError('Action channel missing from frame')
        if a['kind'] not in ('measure','clear','move'): raise ValueError('Unsupported action kind')
        if math.dist(a['position'],frames[i]['q'])>1e-5: raise ValueError('Action/frame position mismatch')
        if data['single'][i-1]['start'] != i or data['single'][i-1]['end'] != i:
            raise ValueError('Single-step numbering mismatch')
    covered = []
    for g in data['groups']:
        if g['start'] > g['end']: raise ValueError('Empty/reversed group')
        covered.extend(range(g['start'],g['end']+1))
    if covered != list(range(1,n+1)): raise ValueError('Groups must cover all actions in order without overlap')
    for g in data['groups'] + data['single']:
        for k in ('title','action','feedback','why'):
            if not isinstance(g.get(k),str): raise ValueError('Missing explanation text: '+k)
        if g.get('focus',0) not in ids | {0}: raise ValueError('Invalid focus ID')
    if frames[-1]['complete'] and any(c['status'] in ('unknown','found') for c in frames[-1]['channels']):
        raise ValueError('Complete flag contradicts unfinished channels')
    for s in data.get('case',{}).get('sources',[]):
        point(s['position'])
        if s['channel'] not in ids: raise ValueError('Truth channel missing from state')
    for k,v in data.get('scene',{}).items():
        if k.endswith('_radius') or k in ('bearing_length','angle_error_deg'):
            if v is not None and (not isinstance(v,(int,float)) or v<=0): raise ValueError('Invalid scene parameter '+k)
    return n


def build(data, output, title=None, q3_defaults=False, standalone=False):
    n=validate(data)
    data=dict(data)
    data['scene']=dict(Q3 if q3_defaults else {}, **data.get('scene',{}))
    data.setdefault('case',{})
    data['case'].setdefault('sources',[])
    data.setdefault('options',[])
    data.setdefault('first_end',n+1)
    data.setdefault('note','')
    data.setdefault('initial_why','尚未执行本次记录中的动作。')
    title=title or data.get('title') or '运行全流程回放'
    # Pool exact repeated channel states before display rounding; never drop steps.
    pool=[];index={};frames=[]
    for frame in data['frames']:
        f=dict(frame);ids=[]
        for c in f['channels']:
            key=json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':'))
            if key not in index:index[key]=len(pool);pool.append(c)
            ids.append(index[key])
        f['channels']=ids;frames.append(f)
    data['frames']=frames
    def rounded(x):
        if isinstance(x,float):return round(x,3)
        if isinstance(x,dict):return {k:rounded(v) for k,v in x.items()}
        if isinstance(x,list):return [rounded(v) for v in x]
        return x
    payload=json.dumps(rounded({'data':data,'channelPool':pool}),ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('</','<\\/')
    tag=hashlib.sha256((str(output.resolve())+payload).encode()).hexdigest()[:12]
    template=(Path(__file__).resolve().parents[1]/'assets/replay.html').read_text(encoding='utf-8')
    fragment=template.replace('__REPLAY_ID__',tag).replace('__REPLAY_TITLE__',html.escape(title)).replace('__REPLAY_DATA__',payload)
    if len(fragment.encode('utf-8'))>=1_000_000:
        raise ValueError('Replay exceeds inline size limit. Split into documented continuous ranges; do not silently drop steps.')
    if standalone:
        css=(Path(__file__).resolve().parents[1]/'assets/standalone.css').read_text(encoding='utf-8')
        fragment='<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+html.escape(title)+'</title><style>'+css+'</style></head><body><main>'+fragment+'</main></body></html>'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(fragment,encoding='utf-8')
    assert output.read_text(encoding='utf-8')==fragment
    return {'actions':n,'frames':len(frames),'groups':len(data['groups']),
            'complete':data['frames'][-1]['complete'],'total_s':data['frames'][-1]['time'],
            'output':str(output.resolve()),'bytes':output.stat().st_size,'standalone':standalone,
            'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'validation':'structure, continuity, finite numbers, ending status; not independent physical audit'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--title')
    p.add_argument('--q3-defaults',action='store_true')
    p.add_argument('--standalone',action='store_true',help='Write a complete offline HTML document for a normal browser')
    args=p.parse_args()
    if args.input.resolve()==args.output.resolve(): raise ValueError('Do not overwrite input data')
    data=json.loads(args.input.read_text(encoding='utf-8-sig'))
    receipt=build(data,args.output,args.title,args.q3_defaults,args.standalone)
    receipt['input_sha256']=hashlib.sha256(args.input.read_bytes()).hexdigest()
    args.output.with_suffix('.receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':main()

"""Read Q3 action logs and reconstruct public states without executing a policy."""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

from build_replay import Q3, validate

RULES={
 'initial_1':('第一轮搜索','在首个测点扫描初始频道，获取反馈。'),
 'initial_2':('第二轮搜索','执行该版本安排的第二站测量；是否自适应及其依据需看选点记录。'),
 'joint_cover_scan':('查漏并共享定位','把未知频道覆盖与已知目标服务合并排路，到此站执行测量。'),
 'planned_transverse_scan':('横向补测','按目标可能区域长轴的垂直方向安排观测，提高交会角。'),
 'planned_clearance_scan':('清除停点共享扫描','利用服务目标时的停留位置执行共享扫描。'),
 'current_view':('当前位置补测','在当前地点补测该频道；不增加移动，但检测仍计时。'),
 'certain_here':('原地保证清除','当前点的20米清除圆覆盖目标的保守可能区域。'),
 'certain_center':('到定位中心清除','目标可能区域包围半径已不超过20米，访问包围圆心清除。'),
 'single_center_try':('中心尝试清除','当前规则允许在小范围中心尝试清除；单次成功没有保证。'),
 'finite_cell_clear':('剩余小格清除','局部动作限制触发后，访问剩余可行小格尝试清除。'),
 'certified_multi_clear':('有覆盖保证的多次清除','可行区域被2或3个20米圆覆盖；按计划尝试，成功后停止。'),
 'refined_shared_scan':('试算选择的共享测点','在候选测点及扫描组合之间，依据相容场景的完整续行估计选择。'),
}


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def names(js):return '、'.join('C'+str(j) for j in sorted(set(js))) or '无'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run',required=True,type=Path)
    p.add_argument('--repo',type=Path,help='Optional explicit project-state override; default uses bundled geometry')
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--case',type=Path)
    p.add_argument('--title')
    args=p.parse_args()
    run=args.run.resolve();source=run/'actions.jsonl'
    if args.output.resolve() in [source,run/'result.json',run/'metadata.json']:
        raise ValueError('Refuse to overwrite raw run files')
    records=[json.loads(line) for line in source.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if any(r.get('step')!=i for i,r in enumerate(records,1)):
        raise ValueError('Require complete prefix numbered from step 1; do not replay a suffix from origin')
    result=load(run/'result.json') if (run/'result.json').exists() else {}
    metadata=load(run/'metadata.json') if (run/'metadata.json').exists() else {}
    case={'name':run.parent.name,'sources':[]}
    candidates=[args.case] if args.case else [d/n for d in [run,*list(run.parents)[:3]] for n in ['case.json','cases.json'] if (d/n).exists()]
    case_file=None
    for path in candidates:
        value=load(path)
        if isinstance(value,list):
            matching=[v for v in value if v.get('name')==run.parent.name]
            if len(matching)!=1:
                if args.case:raise ValueError('Explicit case list must uniquely match parent case name')
                continue
            value=matching[0]
        if value.get('name') not in (None,run.parent.name) and not args.case:continue
        case=value;case_file=path;break
    if args.repo:
        geometry=args.repo.resolve()/'experiments/b_q3/probability_patrol/coverage_state.py'
        spec=importlib.util.spec_from_file_location('replay_public_coverage_state',geometry)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        State=module.CoverageInformationState
        geometry_files=[geometry]
    else:
        from q3_state.coverage import CoverageInformationState as State
        geometry=Path(__file__).resolve().parent/'q3_state/coverage.py'
        geometry_files=list(geometry.parent.glob('*.py'))
    state=State()
    def snapshot():
        cs=[]
        for j,c in state.channels.items():
            item={'j':j,'status':c.status}
            if c.status=='found':
                center,radius=c.circle();item.update(center=center,radius=radius,polygon=c.support())
            cs.append(item)
        return {'q':state.position,'time':state.virtual_time_s,'complete':state.complete,
                'seen':sorted(state.ever_seen),'channels':cs}
    frames=[snapshot()];ledger=0.;ledger_complete=True
    for r in records:
        if 'before' in r and 'virtual_time_s' in r['before'] and abs(r['before']['virtual_time_s']-state.virtual_time_s)>1e-6:
            raise ValueError('Before-state timestamp disagrees with history')
        state.update(r,r['response']);frames.append(snapshot())
        if 'independent_costs' in r:ledger+=sum(r['independent_costs'].values())
        else:ledger_complete=False
        if ledger_complete and abs(ledger-state.virtual_time_s)>1e-5:raise ValueError('Logged cost sum disagrees with feedback time')
    if 'total_s' in result and abs(result['total_s']-state.virtual_time_s)>1e-5:raise ValueError('Result time differs from final frame')
    if result.get('success') and not state.complete:raise ValueError('Success result lacks public completion')
    decisions={d['at_action']:d for d in metadata.get('refinement_decisions',[]) if 'at_action' in d}
    def detail(start,end):
        batch=records[start-1:end];a=batch[0];before=frames[start-1];after=frames[end]
        new=set(after['seen'])-set(before['seen'])
        pos=[r['channel'] for r in batch if r['response'].get('measure_result') in ('direction','near')]
        neg=[r['channel'] for r in batch if r['response'].get('measure_result')=='no_signal']
        cleared=[r['channel'] for r in batch if r['response'].get('clear_result')=='success']
        failed=[r['channel'] for r in batch if r['response'].get('clear_result')=='no_target_in_range']
        absent={c['j'] for c in after['channels'] if c['status']=='absent'}-{c['j'] for c in before['channels'] if c['status']=='absent'}
        costs={k:sum(r.get('independent_costs',{}).get(k,0) for r in batch) for k in ['move_s','measure_s','switch_s','success_clear_s','fail_clear_s']}
        q=a['position'];distance=math.dist(before['q'],q)
        action=(f'移动到 ({q[0]:.1f}, {q[1]:.1f}) 米，路程 {distance:.1f} 米；' if distance>1e-5 else '留在当前位置；')
        action+=('检测'+names(r['channel'] for r in batch) if a['kind']=='measure' else f'对C{a["channel"]}执行清除')
        if all('independent_costs' in r for r in batch):
            action+=f'。移动 {costs["move_s"]:.1f} 秒，检测 {costs["measure_s"]:.0f} 秒，切频 {costs["switch_s"]:.0f} 秒，清除操作 {costs["success_clear_s"]+costs["fail_clear_s"]:.0f} 秒。'
        else:action+=f'；本段累计耗时 {after["time"]-before["time"]:.1f} 秒，未记录费用分项。'
        feedback=[]
        for js,prefix in [(new,'新发现'),(set(pos)-new,'再次测到'),(neg,'无信号'),(cleared,'成功清除'),(failed,'清除失败'),(absent,'累计证据排除')]:
            if js:feedback.append(prefix+names(js))
        if start==end and a['response'].get('measure_result')=='direction':feedback.append(f'方位 {a["response"]["svd_deg"]:.2f}°')
        if after['complete']:feedback.append('公开状态确认本局完成')
        code=a.get('reason','unrecorded');title,rule=RULES.get(code,(code,'日志未记录可解释的选择依据。'))
        why=a.get('why') or a.get('explanation') or ('规则说明：'+rule if code in RULES else rule)
        d=decisions.get(start-1)
        if d:
            why+=f' 决策日志选择 {d.get("chosen","未记录")}。'
            if 'predicted_saving_s' in d:why+=f'相对原动作预测节省 {d["predicted_saving_s"]:.1f} 秒（并非实际节省）。'
            if 'fallback' in d:why+='试算失败，按日志回退原动作。'
        if code=='initial_2' and metadata.get('selected_second'):
            selected=metadata['selected_second'];why+=f' 选点记录：{selected.get("id","未命名")}。'
        focus=(cleared or failed or sorted(new) or pos or [a['channel']])[0]
        return {'start':start,'end':end,'title':title,'action':'动作：'+action,
                'feedback':'反馈：'+('；'.join(feedback) or '见原始反馈记录')+'。','why':'理由：'+str(why),'focus':focus}
    groups=[];start=1
    for i in range(1,len(records)):
        a,b=records[i-1:i+1]
        same=a['kind']==b['kind']=='measure' and a.get('reason')==b.get('reason') and a.get('phase')==b.get('phase') and math.dist(a['position'],b['position'])<1e-6
        if not same or i in decisions:groups.append(detail(start,i));start=i+1
    if records:groups.append(detail(start,len(records)))
    inputs=[source,*geometry_files]+([case_file] if case_file else [])+[f for f in [run/'result.json',run/'metadata.json'] if f.exists()]
    if args.output.resolve() in {f.resolve() for f in inputs}:
        raise ValueError('Refuse to overwrite any input file')
    data={'title':args.title or run.name+' · '+case.get('name',run.parent.name),
          'case':case,'scene':Q3,'frames':frames,'groups':groups,'single':[detail(i,i) for i in range(1,len(records)+1)],
          'actions':[{'kind':r['kind'],'channel':r['channel'],'position':r['position'],
            'result':r['response'].get('measure_result',r['response'].get('clear_result')),'bearing':r['response'].get('svd_deg')} for r in records],
          'options':[],'first_end':len(records)+1,
          'initial_why':'按运行日志重建；未运行或更改策略。',
          'note':('已确认完成。' if state.complete else '记录结束，未确认完成。')+'可能区域按公开反馈重建；真值只用于讲解。',
          'provenance':{'adapter':'adapt_q3.py','geometry':str(geometry),'ledger_checked':ledger_complete,
            'inputs':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs},
            'reason_source':'logged explanation if present; otherwise documented reason-code mapping; unknown reasons explicitly missing'}}
    validate(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'actions':len(records),'frames':len(frames),'groups':len(groups),'complete':state.complete,'total_s':state.virtual_time_s,'output':str(args.output)},ensure_ascii=False))


if __name__=='__main__':main()

"""Prepare a user-started demo; no model calls and no chat message submission."""
import argparse,io,json,shutil,tarfile,time,hashlib
from pathlib import Path
import httpx
from omnigent.spec.parser import parse
from omnigent.spec.validator import validate
from physicslab.request_budget import SharedRequestBudget,validate_demo_authorization
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--create-session',action='store_true');args=parser.parse_args()
record_path=root/'evidence/omnigent-demo.json'
if record_path.exists():raise FileExistsError('Demo already created; preserve its session and budget')
config=json.loads((root/'configs/codex-demo.json').read_text())
validate_demo_authorization(root,config)
target=root/'.runtime/user-demo-agent'
if not args.create_session:
    if target.exists():raise FileExistsError('Preserve previous demo package')
    shutil.copytree(root/'agents/lab',target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    style='''
User-started live research demonstration:
- Use English for visible messages and child titles.
- The user's question concerns Harness mechanisms, with model pass rate,
  time and token use as outcomes. Raw versus structured diagnostics is the
  implemented example mechanism, not the entire research agenda.
- Begin each stage with one brief sentence: Goal, Plan, Experiment, Analysis,
  Validation. Explain what this stage does and which evidence drives the next.
- Keep technical detail in native tool records. Never hide failures or recovery.
- No general mechanism benefit, causal time saving or token reduction claim from
  one acceptance pair. Tool seconds are not total model or workflow time.
- Model temperature/seed are not exposed as controllable matched fields. Report
  these limitations rather than inventing measurements or controls.
- After an automatic child completion notice, collect your own sys_read_inbox;
  do not poll while a child is pending. Report the actual final result.
- Stop on validated or budget, quota, isolation error. All original role and
  fixed-evaluation constraints remain in force.
'''
    for p in target.rglob('AGENTS.md'):
        p.write_text(p.read_text().replace('provide a concise Chinese report with run IDs','provide a concise English report with run IDs')+style)
    spec=parse(target,expand_env=False);result=validate(spec)
    if not result.valid:raise ValueError([(x.path,x.message) for x in result.errors])
    gate=SharedRequestBudget(max_requests=config['max_model_requests'],wall_seconds=config['max_wall_seconds'],journal=root/'.runtime/demo-requests.jsonl',start_on_first_request=True)
    gate.close()
    proof={'prepared_at_unix':time.time(),'authorization':config,'config_sha256':hashlib.sha256((root/'configs/codex-demo.json').read_bytes()).hexdigest(),'model_requests':0,'clock_started':False,'user_starts_by_sending_goal':True,'historical_journals_preserved':True}
    (root/'evidence/demo-authorization.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'prepared':True,'model_requests':0,'clock_started':False}))
else:
    if not target.is_dir():raise RuntimeError('Prepare bundle first')
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for p in sorted(target.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:archive.add(p,arcname=str(p.relative_to(target)))
    with httpx.Client(base_url='http://127.0.0.1:6768',timeout=30) as client:
        hosts=client.get('/v1/hosts');hosts.raise_for_status()
        online=[h for h in hosts.json()['hosts'] if h['host_id']=='b4930df7cea24c0f93b5c03f51aa9f3e' and h['status']=='online']
        if len(online)!=1:raise RuntimeError('Dedicated project host not online')
        metadata={'title':'Pufibara Lab: Live Harness Research','host_id':online[0]['host_id'],'workspace':str(root/'.runtime/agent-work'),'reasoning_effort':'low'}
        response=client.post('/v1/sessions',data={'metadata':json.dumps(metadata)},files={'bundle':('pufibara-demo.tar.gz',buffer.getvalue(),'application/gzip')});response.raise_for_status()
        sid=response.json().get('id') or response.json().get('session_id')
        if not sid:raise RuntimeError('Native session ID missing')
        items=client.get(f'/v1/sessions/{sid}/items',params={'limit':100});items.raise_for_status()
        if items.json()['data']:raise RuntimeError('New demo session must be empty')
    caps=json.loads((root/'.runtime/capabilities.json').read_text())
    rows=[json.loads(line) for line in (root/'.runtime/demo-requests.jsonl').read_text().splitlines()]
    assert all(x['event']!='budget_started' for x in rows)
    assert max(x.get('reserved_requests',0) for x in rows)==0
    broker_id=caps.get('session_id')
    record={'parent_session_id':sid,'kind':'real_user_started_demo_awaiting_goal','bundle':'.runtime/user-demo-agent','created_at_unix':time.time(),'message_submitted':False,'model_requests':0,'clock_started':False,'url':f'http://127.0.0.1:6768/c/{sid}','broker_session_id':broker_id,'phase':'demo'}
    record_path.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))

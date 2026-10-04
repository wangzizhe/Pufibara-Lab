"""Human-operated local control: six real steps, measured clicks, no hidden replay."""
import argparse
import io
import json
import subprocess
import tarfile
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
from physicslab.contracts import identifier

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('session_id');parser.add_argument('--port',type=int,default=6769);parser.add_argument('--auto-session',required=True);parser.add_argument('--preview',action='store_true');args=parser.parse_args()
identifier(args.session_id);identifier(args.auto_session)
capinfo=json.loads((root/'.runtime/capabilities.json').read_text())
if capinfo['session_id'] != args.session_id:raise RuntimeError('Trusted host/broker must be prepared for this manual session')
file=root/('.runtime/manual-preview.json' if args.preview else '.runtime/manual-ui.json')
if file.exists():
 state=json.loads(file.read_text())
 if state['session_id']!=args.session_id:raise RuntimeError('Prior measurement exists; preserve it before preparing another session')
else:
 state={'session_id':args.session_id,'auto_session':args.auto_session,'prepared_at':time.time(),'started_at':None,'events':[],'roots':[],'roles':{},'accepted':False,'finished':False,'operator':'human_ui_clicks','condition':'cooling-sign-v1-gpt6.1sol-matched-logs-max2-fixed-evaluator','setup_seconds':None,'setup_operator':'codex_local_preparation'}
lock=threading.Lock()
def persist():
 stage=file.with_suffix('.tmp');stage.write_text(json.dumps(state,ensure_ascii=False,indent=2));stage.replace(file)
 if args.preview:return
 folder=root/'evidence/measurements';folder.mkdir(exist_ok=True)
 (folder/('manual-'+args.session_id+'.json')).write_text(json.dumps(state,ensure_ascii=False,indent=2))
def snapshot():
 broker=json.loads((root/'evidence/sessions'/args.session_id/'session.json').read_text())
 statuses={}
 with httpx.Client(base_url='http://127.0.0.1:6768',timeout=10) as c:
  for sid in state['roots']:
   response=c.get('/v1/sessions/'+sid);response.raise_for_status();statuses[sid]=response.json().get('status')
 journal=[json.loads(line) for line in (root/'.runtime/research-requests.jsonl').read_text().splitlines()]
 auth=next((r for r in reversed(journal) if r.get('event')=='budget_amended'),journal[0])
 count=max(r.get('reserved_requests',0) for r in journal)
 idle=all(s=='idle' for s in statuses.values())
 ready=count<auth['max_requests'] and time.time()<auth['deadline_unix']
 phase=broker['stage'];roles=list(state['roles'].values())
 enabled={'plan':state['started_at'] is None and phase=='planning' and ready,
 'accept':phase=='experiment' and not state['accepted'] and idle,
 'initial':state['accepted'] and phase=='experiment' and 'executor' not in roles and ready,
 'analysis':phase=='analysis' and 'analyst' not in roles and idle and ready,
 'followup':phase=='followup' and roles.count('executor')==1 and idle and ready,
 'report':phase=='validated' and idle and not state['finished'],
 'retry':any(v=='failed' for v in statuses.values()) and ready}
 if args.preview:enabled={key:False for key in enabled}
 return {'preview':args.preview,'stage':phase,'enabled':enabled,'events':state['events'],'statuses':statuses,'request_count':count,'request_limit':auth['max_requests'],'seconds_left':round(auth['deadline_unix']-time.time()),'elapsed_seconds':round(time.time()-state['started_at']) if state['started_at'] else None,'finished':state['finished'],'plans':broker['plans'],'analysis':broker['analysis'],'trials':[{k:t.get(k) for k in ('trial_id','config','finished','evaluation','final_run_id')} for t in broker['trials']]}
def authorization_text():
 journal=[json.loads(line) for line in (root/'.runtime/research-requests.jsonl').read_text().splitlines()]
 auth=next((r for r in reversed(journal) if r.get('event')=='budget_amended'),journal[0])
 return f"Phase total: {auth['max_requests']} requests / {auth['wall_seconds']/60:g} minutes; retain original start and consumption"
def launch(role, message):
 path=root/'agents/lab/agents'/role
 bundle=io.BytesIO()
 with tarfile.open(fileobj=bundle,mode='w:gz') as tar:
  for p in sorted(path.rglob('*')):
   if p.is_file():tar.add(p,arcname=str(p.relative_to(path)))
 metadata={'title':'Manual research trigger: '+role,'host_id':'b4930df7cea24c0f93b5c03f51aa9f3e','workspace':str(root/'.runtime/agent-work')}
 with httpx.Client(base_url='http://127.0.0.1:6768',timeout=60) as c:
  response=c.post('/v1/sessions',data={'metadata':json.dumps(metadata)},files={'bundle':('manual-role.tar.gz',bundle.getvalue(),'application/gzip')});response.raise_for_status()
  sid=response.json().get('id') or response.json().get('session_id')
  if not sid:raise RuntimeError('No native session ID returned')
  state['roots'].append(sid);state['roles'][sid]=role;persist()
  response=c.post('/v1/sessions/'+sid+'/events',json={'type':'message','data':{'role':'user','content':[{'type':'input_text','text':message+' Retain '+authorization_text()+'. Model requests include role reasoning, failures and retries. End the turn after delegation and wait for automatic completion, without polling. Runtime checks Modeler separation; do not call session-discovery/history tools.'}]}});response.raise_for_status()
 return sid
messages={
 'plan':('planner','This is a real human-triggered comparison. Record a falsifiable diagnostics hypothesis and at least two costed candidates; select matched raw/structured trials. Fix cooling-sign-v1, one initial trial per arm, replicate=0,max_attempts=2 and unchanged checking/simulation/behavior evaluation. Twelve deterministic runs total, reserve six for follow-up. Do not execute experiments.'),
 'initial':('executor','The human accepted the initial broker plan. Execute matched initial trials and stop at status=analysis for human analysis triggering. Do not repair models yourself; delegate independent Modelers and finish_trial afterward.'),
 'analysis':('analyst','The human triggered initial analysis. Use actual status run IDs to record support, limitations, evidence-driven adjustment and a feasible follow-up. Retain task/base model/evaluation and twelve-run tool ceiling. Do not invent mechanism benefits or execute follow-up.'),
 'followup':('executor','The human triggered the recorded evidence-driven follow-up. Execute only the accepted broker plan and stop at validated. Independent Modelers receive their own public task, never another trial source or answer.')}
PAGE='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Manual research workflow timer</title><style>body{font:18px system-ui;background:#0b1825;color:#e6f1fa;max-width:1050px;margin:50px auto;padding:20px}h1{font-size:34px}p{line-height:1.8}button{display:block;width:100%;padding:18px;margin:12px 0;text-align:left;background:#214d68;color:white;border:1px solid #49788d;border-radius:8px;font:18px system-ui;cursor:pointer}button:disabled{opacity:.35;cursor:default}pre{font-size:14px;white-space:pre-wrap;background:#142a3b;padding:20px;border-radius:8px}.muted{color:#9cb6c9}#error{color:#ffbc91}</style><h1>Human-triggered research loop</h1><p>Click each stage; the next opens only after the Agent finishes. Waits count toward elapsed time. Preserve clicks, failures and retries. Refreshing does not reset timing or budgets.</p><p class="muted">Preparation is recorded separately. Existing subscription only; this run shares total 200 requests / 60 minutes with the automatic path. Consumption is retained. This operation alone does not establish research speedup.</p><div id="summary"></div><button data-action="plan">1 · Start timing and planning</button><button data-action="accept">2 · Review and accept initial plan</button><button data-action="initial">3 · Run initial experiments</button><button data-action="analysis">4 · Analyze results and select follow-up</button><button data-action="followup">5 · Run follow-up validation</button><button data-action="report">6 · Save report and end timing</button><button data-action="retry">Recover if needed (extra click recorded)</button><p id="error"></p><pre id="evidence">Reading actual state...</pre><script>async function refresh(){try{const s=await(await fetch('/state')).json();document.querySelector('#summary').textContent=(s.preview?'Read-only preview; opens after automatic completion · ':'')+'Stage: '+s.stage+' · requests '+s.request_count+'/'+s.request_limit+' · authorization remaining '+s.seconds_left+' seconds · elapsed '+(s.elapsed_seconds??'not started')+' seconds';document.querySelectorAll('button').forEach(b=>b.disabled=!s.enabled[b.dataset.action]);document.querySelector('#evidence').textContent=JSON.stringify({plansToReview:s.plans,evidenceDrivenAdjustment:s.analysis,trials:s.trials,roles:s.statuses,events:s.events},null,2);if(s.finished)document.querySelector('#error').textContent='Report and measured timing saved. Return to Codex for review.'}catch(e){document.querySelector('#error').textContent=String(e)}}document.querySelectorAll('button').forEach(b=>b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json','X-Lab-Action':'human-click'},body:JSON.stringify({action:b.dataset.action})});const v=await r.json();document.querySelector('#error').textContent=v.error||''}catch(e){document.querySelector('#error').textContent=String(e)}refresh()});refresh();setInterval(refresh,5000);</script></html>'''
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*unused):pass
 def send(self,value,status=200,html=False):
  content=value.encode() if html else json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
 def do_GET(self):
  if self.headers.get('Host')!=f'127.0.0.1:{args.port}':return self.send({'error':'Host rejected'},403)
  if self.path=='/':
   page=PAGE.replace('total 200 requests / 60 minutes',authorization_text())
   return self.send(page,html=True)
  if self.path=='/state':
   try:
    with lock:return self.send(snapshot())
   except Exception as e:return self.send({'error':type(e).__name__},500)
  return self.send({'error':'Unknown endpoint'},404)
 def do_POST(self):
  if args.preview:return self.send({'error':'Preview only; automatic loop is still running'},403)
  if self.path!='/action' or self.headers.get('Host')!=f'127.0.0.1:{args.port}' or self.headers.get('Origin')!=f'http://127.0.0.1:{args.port}' or self.headers.get('X-Lab-Action')!='human-click':return self.send({'error':'Local UI action required'},403)
  with lock:
   try:
    length=int(self.headers.get('Content-Length','0'))
    if not 0<length<1000:raise ValueError('Invalid body')
    action=json.loads(self.rfile.read(length))['action']; current=snapshot()
    event={'at_unix':time.time(),'action':action,'prior_stage':current['stage']};state['events'].append(event)
    if not current['enabled'].get(action):raise ValueError('Action unavailable; wait for actual stage and remaining authorization')
    if action=='plan':state['started_at']=time.time();state['ready_wait_seconds']=state['started_at']-state['prepared_at']
    if action=='plan':
     prep=root/'evidence/manual-preparation.json'
     state['setup_seconds']=json.loads(prep.read_text()).get('elapsed_seconds') if prep.exists() else None
    if action in messages:role,message=messages[action];event['session_id']=launch(role,message)
    elif action=='retry':
     failed=[sid for sid,value in current['statuses'].items() if value=='failed']
     sid=failed[-1]
     response=httpx.post('http://127.0.0.1:6768/v1/sessions/'+sid+'/events',json={'type':'message','data':{'role':'user','content':[{'type':'input_text','text':'The human clicked recovery. Check current broker stage and completed records; continue unfinished role work without repeating accepted plans or finished trials or resetting budgets. Use independent Modeler conversations verified by runtime. Wait for child completion; do not poll.'}]}},timeout=60);response.raise_for_status();event['session_id']=sid
    elif action=='accept':state['accepted']=True
    elif action=='report':
     native={'parent_session_id':state['roots'][0],'root_session_ids':state['roots'],'root_roles':state['roles'],'kind':'real_human_triggered_workflow'}
     (root/'evidence/omnigent-manual.json').write_text(json.dumps(native,indent=2))
     subprocess.run([str(root/'.venv/bin/python'),str(root/'scripts/collect_omnigent_evidence.py'),'--manual'],check=True,capture_output=True)
     subprocess.run([str(root/'.venv/bin/python'),str(root/'scripts/build_research_report.py'),args.session_id,'--manual'],check=True,capture_output=True)
     state.update(finished=True,ended_at=time.time(),elapsed_seconds=time.time()-state['started_at'],operator_actions=len(state['events']),report=f'evidence/sessions/{args.session_id}/report.md')
    event['status']='applied';persist();self.send({'ok':True})
   except Exception as e:
    if 'event' in locals():event.update(status='failed',error_type=type(e).__name__)
    persist();self.send({'error':str(e) if isinstance(e,ValueError) else type(e).__name__},400)
persist();print(f'Manual workflow ready at http://127.0.0.1:{args.port}/; no model request until human clicks.',flush=True)
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()

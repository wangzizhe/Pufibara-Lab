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
 return f"本阶段总{auth['max_requests']}请求/{auth['wall_seconds']/60:g}分钟，保留原起算与已用计数"
def launch(role, message):
 path=root/'agents/lab/agents'/role
 bundle=io.BytesIO()
 with tarfile.open(fileobj=bundle,mode='w:gz') as tar:
  for p in sorted(path.rglob('*')):
   if p.is_file():tar.add(p,arcname=str(p.relative_to(path)))
 metadata={'title':'手工触发科研 · '+role,'host_id':'b4930df7cea24c0f93b5c03f51aa9f3e','workspace':str(root/'.runtime/agent-work')}
 with httpx.Client(base_url='http://127.0.0.1:6768',timeout=60) as c:
  response=c.post('/v1/sessions',data={'metadata':json.dumps(metadata)},files={'bundle':('manual-role.tar.gz',bundle.getvalue(),'application/gzip')});response.raise_for_status()
  sid=response.json().get('id') or response.json().get('session_id')
  if not sid:raise RuntimeError('No native session ID returned')
  state['roots'].append(sid);state['roles'][sid]=role;persist()
  response=c.post('/v1/sessions/'+sid+'/events',json={'type':'message','data':{'role':'user','content':[{'type':'input_text','text':message+' 沿用'+authorization_text()+'，模型请求包括各角色推理和失败重试。派发子角色后结束当前轮等自动通知，不轮询；runtime自动检查建模会话分离，不调用会话发现/历史工具。'}]}});response.raise_for_status()
 return sid
messages={
 'plan':('planner','这是实际真人手工触发对照。提出并记录日志机制的可证伪假设、至少两个成本候选并选择 matched raw/structured 对照。固定任务cooling-sign-v1，初始 raw/structured 各一次，replicate=0,max_attempts=2，既定检查/仿真/行为评价不可更改；总确定性工具运行12，留6次后续预算。不要执行实验。'),
 'initial':('executor','真人已接受 broker 初始计划。执行初始匹配试次，到 status=analysis 时停止，等待人工触发分析。不要自行修复模型，各trial给独立modeler，完成后finish_trial。'),
 'analysis':('analyst','真人触发初次结果分析。依据 status 真实 run IDs 记录支持程度、限制、结果如何改变下一步以及可执行 followup。适配同任务/基础模型/评价，工具总额度12，不编造机制收益；不要执行后续验证。'),
 'followup':('executor','真人触发已记录的结果驱动 followup。只执行 broker 接受的后续计划，到 validated 时停止。独立 modeler 接收本 trial 公共任务，不能继承别的trial源码或答案。')}
PAGE='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>手工科研流程计时</title><style>body{font:18px system-ui;background:#0b1825;color:#e6f1fa;max-width:1050px;margin:50px auto;padding:20px}h1{font-size:34px}p{line-height:1.8}button{display:block;width:100%;padding:18px;margin:12px 0;text-align:left;background:#214d68;color:white;border:1px solid #49788d;border-radius:8px;font:18px system-ui;cursor:pointer}button:disabled{opacity:.35;cursor:default}pre{font-size:14px;white-space:pre-wrap;background:#142a3b;padding:20px;border-radius:8px}.muted{color:#9cb6c9}#error{color:#ffbc91}</style><h1>手工触发科研闭环</h1><p>每一步由你点击；Agent 完成后下一步才开放。等待时间计入实际墙钟，点击、错误和重试全部保留。刷新页面不会重置计时或预算。</p><p class="muted">准备环境单独记录。只使用现有订阅；本轮与自动路径共享总 200 次／60 分钟，已用额度不会清零。不能把本次操作估计为科研提速。</p><div id="summary"></div><button data-action="plan">1 · 开始计时并触发规划</button><button data-action="accept">2 · 核对并接受真实初始方案</button><button data-action="initial">3 · 触发初次实验</button><button data-action="analysis">4 · 触发结果分析与下一计划</button><button data-action="followup">5 · 触发后续验证</button><button data-action="report">6 · 生成报告并结束计时</button><button data-action="retry">异常恢复（如需要；额外点击计入动作）</button><p id="error"></p><pre id="evidence">正在读取实际状态…</pre><script>async function refresh(){try{const s=await(await fetch('/state')).json();document.querySelector('#summary').textContent=(s.preview?'只读预览，自动闭环完成后开放 · ':'')+'阶段：'+s.stage+' · 总请求 '+s.request_count+'/'+s.request_limit+' · 授权剩余 '+s.seconds_left+' 秒 · 本轮计时 '+(s.elapsed_seconds??'未开始')+' 秒';document.querySelectorAll('button').forEach(b=>b.disabled=!s.enabled[b.dataset.action]);document.querySelector('#evidence').textContent=JSON.stringify({接受前请核对方案:s.plans,结果驱动调整:s.analysis,实际试次:s.trials,实际角色:s.statuses,操作记录:s.events},null,2);if(s.finished)document.querySelector('#error').textContent='报告和真实计时已保存，返回 Codex 继续核对。'}catch(e){document.querySelector('#error').textContent=String(e)}}document.querySelectorAll('button').forEach(b=>b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/action',{method:'POST',headers:{'Content-Type':'application/json','X-Lab-Action':'human-click'},body:JSON.stringify({action:b.dataset.action})});const v=await r.json();document.querySelector('#error').textContent=v.error||''}catch(e){document.querySelector('#error').textContent=String(e)}refresh()});refresh();setInterval(refresh,5000);</script></html>'''
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*unused):pass
 def send(self,value,status=200,html=False):
  content=value.encode() if html else json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
 def do_GET(self):
  if self.headers.get('Host')!=f'127.0.0.1:{args.port}':return self.send({'error':'Host rejected'},403)
  if self.path=='/':
   page=PAGE.replace('总 200 次／60 分钟',authorization_text())
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
     response=httpx.post('http://127.0.0.1:6768/v1/sessions/'+sid+'/events',json={'type':'message','data':{'role':'user','content':[{'type':'input_text','text':'真人点击异常恢复。核对broker当前阶段和已完成记录，继续本角色未完成工作，不重复已接受计划或已结束试次，不清零额度；各trial使用独立modeler会话，runtime已自动检查。等待子角色完成通知，不轮询。'}]}},timeout=60);response.raise_for_status();event['session_id']=sid
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

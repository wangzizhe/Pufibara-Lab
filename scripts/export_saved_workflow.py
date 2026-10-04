"""Export a self-contained walkthrough of saved evidence; never call a model."""
from pathlib import Path
import json
import hashlib

root = Path(__file__).resolve().parents[1]
session_path = root / 'evidence/sessions/session-789344082fe64fabadcdb06e415d8d0d/session.json'
tree_path = root / 'evidence/omnigent-demo.json'
measurement_path = root / 'evidence/measurements/demo-observation.json'
session = json.loads(session_path.read_text())
tree = json.loads(tree_path.read_text())
parent_id = tree['parent_session_id']
folder = root / 'evidence/omnigent' / parent_id
actors = []
sources = [session_path, tree_path, measurement_path]
for actor in tree['sessions']:
    path = folder / (actor['id'] + '-items.json')
    sources.append(path)
    actors.append({**actor, 'items': [i for i in json.loads(path.read_text())
                   if i.get('type') in {'message', 'function_call', 'function_call_output'}],
                   'source_path': str(path.relative_to(root))})
payload = {'session': session, 'actors': actors,
    'measurement': json.loads(measurement_path.read_text()),
    'sources': [{'path': str(p.relative_to(root)),
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]}
encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
html = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pufibara Lab — Saved Research Walkthrough</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f6f7fb;color:#172033;font:15px/1.5 system-ui,-apple-system,sans-serif}main{max-width:1160px;margin:auto;padding:32px 28px}h1{font-size:32px;letter-spacing:-1px;margin:12px 0 5px}h2{font-size:20px;margin:0 0 12px}h3{font-size:16px;margin:0 0 8px}.badge{display:inline-block;padding:5px 10px;border-radius:20px;background:#e7eafd;color:#4338ca;font-size:12px;font-weight:650}.lead{color:#596579;margin:0 0 22px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric,.panel{background:white;border:1px solid #e0e4ee;border-radius:12px;padding:18px}.metric b{display:block;font-size:23px}.metric span,.muted{font-size:12px;color:#667287}nav{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0 16px}button{border:1px solid #d8ddeb;border-radius:8px;padding:10px 14px;background:white;color:#3f4a60;cursor:pointer;font:inherit}button.active{background:#4338ca;color:white;border-color:#4338ca}button:hover{border-color:#4338ca}.grid{display:grid;grid-template-columns:1.75fr 1fr;gap:16px}.quote{max-height:360px;overflow:auto;white-space:pre-wrap;background:#f8f9fd;border-left:3px solid #6366f1;padding:16px;margin:10px 0}.source{font:11px/1.5 ui-monospace,monospace;color:#65748b;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{text-align:left;border-bottom:1px solid #e6e9f1;padding:9px 6px;font-size:13px}th{color:#626e83;font-size:12px}.role{padding:8px 0;border-bottom:1px solid #f0f1f6;display:flex;justify-content:space-between;gap:8px}.role small{color:#6e798c}.notice{border-radius:8px;background:#fff6e8;color:#795326;padding:12px;margin-top:14px;font-size:12px}details{background:white;border:1px solid #e0e4ee;border-radius:8px;padding:12px;margin:10px 0}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:480px;overflow:auto;background:#f8f9fd;padding:14px;font:12px/1.55 ui-monospace,monospace}a{color:#4338ca}.section{margin-top:26px}footer{font-size:12px;color:#69758b;margin:20px 0}@media(max-width:760px){main{padding:20px 16px}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}h1{font-size:27px}}
</style></head><body><main>
<span class="badge">SAVED RUN · OFFLINE EVIDENCE · NO LLM CALLS</span>
<h1>One research goal. An evidence-driven loop.</h1>
<p class="lead">Pufibara Lab · Omnigent orchestration → Modelica experiments → result-driven follow-up</p>
<div class="metrics" id="metrics"></div>
<nav id="stages" aria-label="Recorded research stages"></nav>
<div class="grid"><section class="panel" id="stage"></section><aside class="panel"><h2>Real Agent handoffs</h2><div id="roles"></div><div class="notice">These are saved native sessions. This page does not run agents, connect to a model or simulate a new discovery.</div></aside></div>
<section class="section"><h2>Inspect all saved Agent records</h2><p class="muted">Expand a session for original messages and tool calls from this English run. Session IDs connect this view to the repository evidence.</p><div id="records"></div></section>
<details><summary>Source files and hashes</summary><pre id="provenance"></pre></details>
<footer>Recorded evidence walkthrough, not the Omnigent application or a live research service. Original source files, compiler logs, trajectories, fixed evaluations and failure records are in the repository. No general mechanism benefit, overall speedup or token saving is established.</footer>
</main><script>
const data=PAYLOAD;
const repo='https://github.com/wangzizhe/Pufibara-Lab/blob/main/';
const root=data.actors.find(a=>a.parent_session_id===null);
const messages=root.items.filter(i=>i.type==='message');
const text=i=>(i.content||[]).map(c=>c.text||'').join('\n');
const find=s=>messages.find(i=>text(i).startsWith(s));
const stages=[
 {label:'1 · Goal',title:'A falsifiable Harness research question',message:messages.find(i=>i.role==='user'&&!text(i).startsWith('[System:')),note:'Actual user goal; all following stages are saved evidence.'},
 {label:'2 · Plan',title:'Compare candidates and reserve follow-up budget',message:find('Experiment: Plan'),plan:data.session.plans[0]},
 {label:'3 · Experiment',title:'Run a matched raw/structured pair',message:find('Both arms passed in two attempts.'),trials:data.session.trials.filter(t=>t.plan_id==='initial-logs')},
 {label:'4 · Analyze',title:'Use the initial result to choose the next experiment',message:find('Validation: Follow-up'),plan:data.session.plans[1]},
 {label:'5 · Validate',title:'Execute the fresh pair selected from evidence',message:find('Validation: The repeat reached'),trials:data.session.trials.filter(t=>t.plan_id==='repeat-logs-01')},
 {label:'6 · Result',title:'Equal acceptance; timing order reversed',message:messages.filter(i=>i.role==='assistant').at(-1),trials:data.session.trials}
];
function node(tag,value,cls){const e=document.createElement(tag);if(value!==undefined)e.textContent=value;if(cls)e.className=cls;return e}
const m=data.measurement;
for(const [value,label] of [['4','Completed trials'],['12','Deterministic tool runs'],[String(data.actors.length),'Native Agent sessions'],[String(m.goal_to_final_summary_seconds)+' s','Recorded goal-to-summary span']]){const e=node('div',undefined,'metric');e.append(node('b',value),node('span',label));document.querySelector('#metrics').append(e)}
function table(trials){const t=node('table');const header=node('tr');for(const label of ['Pair / feedback','Attempts','Final verdict','Tool seconds'])header.append(node('th',label));t.append(header);for(const a of trials){const tr=node('tr');for(const v of [(a.config.replicate===0?'Initial':'Follow-up')+' / '+a.config.diagnostics,a.attempts.length,a.evaluation.all_passed?'All 3 passed':'See record',a.tool_seconds.toFixed(3)])tr.append(node('td',v));t.append(tr);const link=node('a',a.final_run_id);link.href=repo+'evidence/runs/'+a.final_run_id+'/result.json';link.target='_blank';const row=node('tr');const td=node('td');td.colSpan=4;td.append(link);row.append(td);t.append(row)}return t}
function show(index){document.querySelectorAll('nav button').forEach((b,i)=>b.classList.toggle('active',i===index));const s=stages[index],out=document.querySelector('#stage');out.replaceChildren(node('h2',s.title));out.append(node('div',index===5?text(s.message).split('\n\n')[0]:text(s.message),'quote'));out.append(node('div',(index===5?'Excerpt from recorded message ':'Recorded message ')+s.message.id+' · timestamp '+s.message.created_at,'source'));if(s.plan){out.append(node('h3','Agent-generated hypothesis (untested proposal)'),node('p',s.plan.hypothesis));if(s.plan.repeat_reason)out.append(node('h3','Evidence-driven selection'),node('p',s.plan.repeat_reason));else out.append(node('h3','Selected from costed candidates'),node('p',s.plan.selected_candidate+' · '+s.plan.candidates.map(c=>c.id+': '+c.estimated_tool_runs+' tool runs').join(' / ')));}if(s.trials)out.append(table(s.trials));out.append(node('div',index===5?'This small study does not establish a general advantage. Tool seconds exclude model/workflow overhead; the 766-second span excludes setup. There is no matched overall speedup or verified token reduction.':'Stage navigation is a presentation of recorded events. It does not trigger new experiments.','notice'));}
for(let i=0;i<stages.length;i++){const b=node('button',stages[i].label);b.addEventListener('click',()=>show(i));document.querySelector('#stages').append(b)}
const ordered=[];function visit(actor,depth){ordered.push({...actor,treeDepth:depth});const children=data.actors.filter(a=>a.parent_session_id===actor.id).sort((a,b)=>Math.min(...a.items.map(i=>i.created_at||Infinity))-Math.min(...b.items.map(i=>i.created_at||Infinity)));for(const child of children)visit(child,depth+1)}visit(root,0);
for(const a of ordered){const role=a.research_role||a.sub_agent_name||'coordinator';const row=node('div',undefined,'role');row.style.paddingLeft=(a.treeDepth*12)+'px';row.append(node('span',(a.treeDepth?'↳ ':'')+role),node('small',a.status+' · '+a.items.length+' saved items'));document.querySelector('#roles').append(row);const d=node('details');d.append(node('summary',role+' · '+a.id));const link=node('a','View original native file');link.href=repo+a.source_path;link.target='_blank';d.append(link,node('pre',JSON.stringify({session_id:a.id,parent_session_id:a.parent_session_id,role,items:a.items},null,2)));document.querySelector('#records').append(d)}
document.querySelector('#provenance').textContent=JSON.stringify(data.sources,null,2);show(5);
</script></body></html>'''
assert all(s['stage']=='validated' for s in [session])
output = root/'docs/research-walkthrough.html'
output.write_text(html.replace('PAYLOAD',encoded))
print(json.dumps({'output':str(output.relative_to(root)),'native_sessions':len(actors),'source_files':len(sources),'model_calls':0}))

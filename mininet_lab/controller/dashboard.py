"""Browser dashboard: select any of 12 hosts and run adaptive experiments."""
from flask import Flask,jsonify,request,render_template_string
from topology.config import HOSTS,HOST_SWITCH,EDGES
PAGE=r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Adaptive Routing AutoPilot - 12 PC Campus</title>
<style>body{font-family:Segoe UI,Arial;margin:22px;background:#f4f6fb;color:#172033}h1{margin-bottom:3px}.sub{color:#5b6578}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.card{background:white;padding:15px;border-radius:12px;box-shadow:0 2px 8px #17203312;margin-top:12px}.big{font-size:23px;font-weight:700}.muted{font-size:13px;color:#687386}button,select,input{padding:9px;margin:4px;border:1px solid #ccd3df;border-radius:7px;background:white}button{background:#1d4ed8;color:white;border:0;cursor:pointer}.secondary{background:#475569}table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:7px;border-bottom:1px solid #e6e9ef;text-align:left}pre{background:#101827;color:#e5e7eb;padding:12px;white-space:pre-wrap}.bad{color:#b91c1c}.warn{color:#a16207}.good{color:#087443}</style></head><body>
<h1>Adaptive Routing AutoPilot</h1><p class="sub">12 selectable PCs · 8 switches · 14 redundant backbone links · Dijkstra · live telemetry · automatic failover</p>
<div class="card"><h3>1. Select source and destination PC</h3>Source <select id="src">{{source_options|safe}}</select> Destination <select id="dst">{{destination_options|safe}}</select> <button onclick="choosePair()">Apply PC pair</button><div class="muted" id="pairmsg">Choose two different PCs.</div></div>
<div class="grid"><div class="card"><div class="muted">Selected communication</div><div class="big" id="pair">--</div><div class="muted" id="ips">--</div></div><div class="card"><div class="muted">Active route</div><div class="big" id="path">--</div></div><div class="card"><div class="muted">End-to-end RTT</div><div class="big" id="rtt">--</div></div><div class="card"><div class="muted">Ping packet loss</div><div class="big" id="loss">--</div></div><div class="card"><div class="muted">Controller</div><div class="big" id="auto">--</div></div></div>
<div class="card"><h3>2. Generate traffic between selected PCs</h3><button onclick="post('/api/traffic/start',{mode:'udp',rate_mbps:25})">Start UDP 25 Mbps</button><button class="secondary" onclick="post('/api/traffic/start',{mode:'tcp',rate_mbps:25})">Start TCP</button><button class="secondary" onclick="post('/api/traffic/stop',{})">Stop traffic</button><button onclick="post('/api/auto',{enabled:true})">Enable automatic routing</button><button class="secondary" onclick="post('/api/auto',{enabled:false})">Pause automatic routing</button></div>
<div class="card"><h3>3. Inject congestion or break a backbone link</h3><select id="edge">{% for e in edges %}<option>{{e}}</option>{% endfor %}</select> Rate Mbps <input id="rate" type="number" value="3" min="1" max="100" style="width:65px"> Delay ms <input id="delay" type="number" value="80" min="0" max="2000" style="width:65px"> Loss % <input id="ploss" type="number" value="1" min="0" max="100" style="width:55px"><br><button onclick="congest()">Apply congestion</button><button class="secondary" onclick="clearCongestion()">Clear congestion</button><button class="secondary" onclick="fail()">Fail link</button><button class="secondary" onclick="recover()">Restore link</button></div>
<div class="card"><h3>4. Live backbone measurements</h3><table><thead><tr><th>Link</th><th>Mbps</th><th>Utilization</th><th>Queue pkts</th><th>Drop Δ</th><th>Loss estimate</th><th>Status</th></tr></thead><tbody id="rows"></tbody></table><div class="muted">Throughput from OVS byte-counter deltas. Queue and drops from Linux traffic-control qdisc. End-to-end RTT/loss from selected source to selected destination.</div></div>
<div class="card"><h3>5. Routing decision</h3><div id="decision">Collecting telemetry…</div><div class="muted" id="action"></div></div>
<script>
const $=id=>document.getElementById(id);
async function post(url,data){let r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let j=await r.json();if(!r.ok||j.error)alert(j.error||JSON.stringify(j));else if(j.path)document.getElementById('pairmsg').textContent='Applied. Initial path: '+j.path.join(' → ');refresh();}
async function choosePair(){if($('src').value===$('dst').value){alert('Select two different PCs');return;}await post('/api/pair',{source:$('src').value,destination:$('dst').value});}
function edgePair(){return $('edge').value.split('-')}function congest(){let [a,b]=edgePair();post('/api/congestion',{a,b,rate_mbps:+$('rate').value,delay_ms:+$('delay').value,loss_pct:+$('ploss').value})}function clearCongestion(){let [a,b]=edgePair();post('/api/congestion/clear',{a,b})}function fail(){let [a,b]=edgePair();post('/api/link/fail',{a,b})}function recover(){let [a,b]=edgePair();post('/api/link/recover',{a,b})}
async function refresh(){try{let d=await(await fetch('/api/status')).json();$('pair').textContent=d.source+' → '+d.destination;$('ips').textContent=d.source_ip+' → '+d.destination_ip;$('path').textContent=(d.active_path||[]).join(' → ');$('rtt').textContent=d.ping.rtt_ms==null?'--':d.ping.rtt_ms.toFixed(2)+' ms';$('loss').textContent=(d.ping.loss_pct??'--')+' %';$('auto').textContent=d.auto?'AUTOMATIC':'PAUSED';$('decision').textContent=d.decision;$('action').textContent=d.action;let html='';for(let [k,v] of Object.entries(d.edges||{})){html+=`<tr><td>${k.join('-')}</td><td>${v.throughput_mbps}</td><td>${v.utilization_pct}%</td><td>${v.queue_packets}</td><td>${v.drop_delta}</td><td>${v.loss_pct}%</td><td class="${v.failed?'bad':v.congested?'warn':'good'}">${v.failed?'FAILED':v.congested?'CONGESTED':'UP'}</td></tr>`}$('rows').innerHTML=html;}catch(e){}}
setInterval(refresh,1000);refresh();
</script></body></html>'''
def create_app(controller):
 app=Flask(__name__)
 opts=''.join(f'<option value="{h}">{h} — {ip.split("/")[0]} ({HOST_SWITCH[h]})</option>' for h,ip in HOSTS.items())
 opts_dst=''.join(f'<option value="{h}" {"selected" if h=="h7" else ""}>{h} — {ip.split("/")[0]} ({HOST_SWITCH[h]})</option>' for h,ip in HOSTS.items())
 @app.get('/')
 def index(): return render_template_string(PAGE,source_options=opts,destination_options=opts_dst,edges=[f'{a}-{b}' for a,b,_,_ in EDGES])
 @app.get('/api/status')
 def status(): return jsonify(controller.last_metrics or {'active_path':controller.policy.active_path,'edges':{},'ping':{},'auto':controller.auto,'decision':'Collecting first sample','action':'--','source':controller.source,'destination':controller.destination})
 @app.post('/api/pair')
 def pair():
  d=request.get_json(force=True)
  try:return jsonify(controller.select_pair(d['source'],d['destination']))
  except Exception as e:return jsonify({'error':str(e)}),400
 @app.post('/api/traffic/start')
 def traffic_start():
  d=request.get_json(force=True)
  try:return jsonify(controller.start_traffic(d.get('mode','udp'),float(d.get('rate_mbps',25))))
  except Exception as e:return jsonify({'error':str(e)}),400
 @app.post('/api/traffic/stop')
 def traffic_stop(): return jsonify(controller.stop_traffic())
 @app.post('/api/auto')
 def auto(): controller.auto=bool(request.get_json(force=True).get('enabled',True)); return jsonify({'auto':controller.auto})
 @app.post('/api/congestion')
 def congestion():
  d=request.get_json(force=True)
  try:return jsonify(controller.apply_congestion(d['a'],d['b'],float(d.get('rate_mbps',3)),int(d.get('delay_ms',80)),float(d.get('loss_pct',1))))
  except Exception as e:return jsonify({'error':str(e)}),400
 @app.post('/api/congestion/clear')
 def clear():
  d=request.get_json(force=True)
  try:return jsonify(controller.clear_congestion(d['a'],d['b']))
  except Exception as e:return jsonify({'error':str(e)}),400
 @app.post('/api/link/fail')
 def fail():
  d=request.get_json(force=True)
  try:return jsonify(controller.fail_link(d['a'],d['b']))
  except Exception as e:return jsonify({'error':str(e)}),400
 @app.post('/api/link/recover')
 def recover():
  d=request.get_json(force=True)
  try:return jsonify(controller.restore_link(d['a'],d['b']))
  except Exception as e:return jsonify({'error':str(e)}),400
 return app

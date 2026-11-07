"""Multi-host telemetry, Dijkstra routing, OpenFlow steering and experiments."""
import csv, os, time, threading, subprocess
from datetime import datetime, timezone
from topology.config import HOSTS, HOST_SWITCH, EDGES
from .telemetry import get_ovs_port_stats, get_qdisc_stats, get_ping_metrics
from .routing import CAPACITY, BASE_DELAY_MS, key, dijkstra, AdaptivePolicy, edge_cost

LOG_DIR=os.path.join(os.path.dirname(os.path.dirname(__file__)),'logs'); os.makedirs(LOG_DIR,exist_ok=True)
SWITCHES=[f's{i}' for i in range(1,9)]
class LabController:
    def __init__(self,net,poll_interval=1.):
        self.net=net; self.poll_interval=poll_interval; self.lock=threading.RLock(); self.running=False; self.auto=True
        self.forced_failed=set(); self.samples={}; self.previous_ports={}; self.previous_qdisc_drops={}; self.last_metrics={}; self.last_ping={}
        self.policy=AdaptivePolicy(); self.last_decision='Starting'; self.last_action='None'; self.traffic_process=None; self.server_process=None
        self.source='h1'; self.destination='h7'; self.links=self._discover_links(); self._init_qdiscs(); self._init_logs()
        self._install_pair_arp(self.source,self.destination)
        initial=dijkstra({},set(),HOST_SWITCH[self.source],HOST_SWITCH[self.destination])['path']
        self.policy.active_path=initial; self._install_path(initial,self.source,self.destination)
        self.previous_congested=set()
    def _discover_links(self):
        result={}
        for link in self.net.links:
            n1,n2=link.intf1.node.name,link.intf2.node.name
            if n1.startswith('s') and n2.startswith('s'):
                k=key(n1,n2); result[k]={'a':k[0],'b':k[1], 'intf_a':link.intf1 if n1==k[0] else link.intf2,'intf_b':link.intf2 if n2==k[1] else link.intf1}
        return result
    def _init_qdiscs(self):
        for r in self.links.values():
            for i in (r['intf_a'],r['intf_b']): subprocess.run(['tc','qdisc','replace','dev',i.name,'root','pfifo','limit','1000'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def _init_logs(self):
        self.csv_path=os.path.join(LOG_DIR,'telemetry.csv'); self.event_path=os.path.join(LOG_DIR,'events.log')
        with open(self.csv_path,'w',newline='') as f:
            csv.writer(f).writerow(['timestamp_utc','source','destination','edge','throughput_mbps','capacity_mbps','utilization_pct','queue_packets','queue_bytes','drops_total','drop_delta','loss_estimate_pct','edge_cost','end_to_end_rtt_ms','end_to_end_ping_loss_pct','congested','active_path','decision','action'])
        open(self.event_path,'w').close()
    def _log_event(self,msg):
        with open(self.event_path,'a') as f: f.write(f"{datetime.now(timezone.utc).isoformat()} | {msg}\n")
    def _switch_port(self,sw,intf): return self.net.get(sw).ports[intf]
    def _port_snapshot(self): return {sw:get_ovs_port_stats(sw) for sw in SWITCHES}
    def _qdisc_snapshot(self):
        out={}
        for e,r in self.links.items():
            a=get_qdisc_stats(r['intf_a'].name); b=get_qdisc_stats(r['intf_b'].name)
            out[e]={'queue_packets':a['backlog_packets']+b['backlog_packets'],'queue_bytes':a['backlog_bytes']+b['backlog_bytes'],'drops_total':a['drops_total']+b['drops_total']}
        return out
    def _edge_failed(self,e):
        r=self.links[e]
        return e in self.forced_failed or not r['intf_a'].isUp() or not r['intf_b'].isUp()
    def _collect(self):
        now=time.monotonic(); ports=self._port_snapshot(); qdiscs=self._qdisc_snapshot(); new={}
        for e,r in self.links.items():
            pa=self._switch_port(r['a'],r['intf_a']); pb=self._switch_port(r['b'],r['intf_b'])
            ca=ports.get(r['a'],{}).get(pa,{}); cb=ports.get(r['b'],{}).get(pb,{})
            oa=self.previous_ports.get((r['a'],pa)); ob=self.previous_ports.get((r['b'],pb)); dt=max(.001,now-self.previous_ports.get(('time',e),now))
            byte_delta=pkt_delta=drop_delta_ovs=0
            for cur,old in ((ca,oa),(cb,ob)):
                if cur and old:
                    byte_delta+=max(0,cur.get('tx_bytes',0)-old.get('tx_bytes',0)); pkt_delta+=max(0,cur.get('tx_packets',0)-old.get('tx_packets',0)); drop_delta_ovs+=max(0,cur.get('tx_dropped',0)-old.get('tx_dropped',0))
            q=qdiscs[e]; olddrops=self.previous_qdisc_drops.get(e,q['drops_total']); drops=max(0,q['drops_total']-olddrops)+drop_delta_ovs; self.previous_qdisc_drops[e]=q['drops_total']
            mbps=byte_delta*8/dt/1_000_000; loss=100*drops/max(1,pkt_delta+drops); cap=CAPACITY[e]; util=min(100.,mbps/cap*100)
            s={'throughput_mbps':round(mbps,3),'capacity_mbps':cap,'utilization_pct':round(util,2),'queue_packets':q['queue_packets'],'queue_bytes':q['queue_bytes'],'drops_total':q['drops_total'],'drop_delta':drops,'loss_pct':round(loss,3),'base_delay_ms':BASE_DELAY_MS[e],'failed':self._edge_failed(e),'congested':util>=70 or q['queue_packets']>=20 or loss>=1}
            new[e]=s; self.previous_ports[(r['a'],pa)]=ca; self.previous_ports[(r['b'],pb)]=cb; self.previous_ports[('time',e)]=now
        src=self.net.get(self.source); dstip=self.net.get(self.destination).IP()
        self.last_ping=get_ping_metrics(src,dstip,count=2); self.samples=new; return new
    def _path_cost(self,samples,path):
        total=0.
        for i in range(len(path)-1):
            e=key(path[i],path[i+1]); s=samples.get(e,{})
            if e not in samples or s.get('failed'): return float('inf')
            total+=edge_cost(s)
        return total
    def _install_pair_arp(self,src,dst):
        a=self.net.get(src); b=self.net.get(dst)
        a.cmd(f'ip neigh replace {b.IP()} lladdr {b.MAC()} nud permanent dev {a.defaultIntf().name}')
        b.cmd(f'ip neigh replace {a.IP()} lladdr {a.MAC()} nud permanent dev {b.defaultIntf().name}')
    def _clear_adaptive_flows(self):
        for sw in SWITCHES: subprocess.run(['ovs-ofctl','-O','OpenFlow13','del-flows',sw,'priority=300'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def _install_path(self,path,src,dst):
        self._clear_adaptive_flows(); self._install_pair_arp(src,dst)
        source=self.net.get(src); dest=self.net.get(dst); srcip=source.IP(); dstip=dest.IP(); srcsw=HOST_SWITCH[src]; dstsw=HOST_SWITCH[dst]
        def intf_to(sw,neighbor):
            if neighbor==src: return source.defaultIntf()
            if neighbor==dst: return dest.defaultIntf()
            r=self.links[key(sw,neighbor)]; return r['intf_a'] if r['a']==sw else r['intf_b']
        for idx,sw in enumerate(path):
            prev=src if idx==0 else path[idx-1]; nxt=dst if idx==len(path)-1 else path[idx+1]
            inp=self._switch_port(sw,intf_to(sw,prev)); outp=self._switch_port(sw,intf_to(sw,nxt))
            self._add_flow(sw,f'priority=300,ip,nw_src={srcip},nw_dst={dstip},in_port={inp},actions=output:{outp}')
            self._add_flow(sw,f'priority=300,ip,nw_src={dstip},nw_dst={srcip},in_port={outp},actions=output:{inp}')
        self._log_event(f'Installed {src}({srcip}) -> {dst}({dstip}) via '+ ' -> '.join(path))
    @staticmethod
    def _add_flow(sw,flow): subprocess.run(['ovs-ofctl','-O','OpenFlow13','add-flow',sw,flow],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def select_pair(self,src,dst):
        if src not in HOSTS or dst not in HOSTS or src==dst: raise ValueError('Choose two different hosts from h1 to h12')
        with self.lock:
            self.stop_traffic(); self.source=src; self.destination=dst
            self._install_pair_arp(src,dst); cand=dijkstra(self.samples,{e for e,s in self.samples.items() if s.get('failed')},HOST_SWITCH[src],HOST_SWITCH[dst])
            if not cand['reachable']: return {'ok':False,'error':'No route between selected PCs'}
            self.policy.active_path=cand['path']; self.policy.last_switch=time.monotonic(); self.policy.better_count=0
            self._install_path(cand['path'],src,dst); self.last_decision='New source/destination pair selected'; self.last_action='Installed initial route'
            return {'ok':True,'source':src,'destination':dst,'path':cand['path']}
    def start_traffic(self,mode='udp',rate_mbps=20):
        self.stop_traffic(); src=self.net.get(self.source); dst=self.net.get(self.destination); dip=dst.IP()
        self.server_process=dst.popen(['iperf3','-s'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(.4)
        args=['iperf3','-c',dip,'-t','36000']
        if mode=='udp': args+=['-u','-b',f'{rate_mbps}M']
        self.traffic_process=src.popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self._log_event(f'Started {mode.upper()} traffic {self.source}->{self.destination}, requested {rate_mbps} Mbps')
        return {'running':True,'source':self.source,'destination':self.destination,'mode':mode,'rate_mbps':rate_mbps}
    def stop_traffic(self):
        for p in (self.traffic_process,self.server_process):
            if p and p.poll() is None: p.terminate()
        self.traffic_process=self.server_process=None; self._log_event('Stopped traffic'); return {'running':False}
    def apply_congestion(self,a,b,rate_mbps=3,delay_ms=80,loss_pct=1):
        e=key(a,b)
        if e not in self.links: raise ValueError('Unknown backbone link')
        for i in (self.links[e]['intf_a'],self.links[e]['intf_b']): subprocess.run(['tc','qdisc','replace','dev',i.name,'root','netem','rate',f'{rate_mbps}mbit','delay',f'{delay_ms}ms','loss',f'{loss_pct}%','limit','100'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self._log_event(f'Congestion injected on {e}'); return {'edge':e,'rate_mbps':rate_mbps,'delay_ms':delay_ms,'loss_pct':loss_pct}
    def clear_congestion(self,a,b):
        e=key(a,b)
        for i in (self.links[e]['intf_a'],self.links[e]['intf_b']): subprocess.run(['tc','qdisc','replace','dev',i.name,'root','pfifo','limit','1000'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self._log_event(f'Congestion cleared on {e}'); return {'edge':e,'cleared':True}
    def fail_link(self,a,b):
        e=key(a,b); r=self.links[e]; r['intf_a'].ifconfig('down'); r['intf_b'].ifconfig('down'); self.forced_failed.add(e); self._log_event(f'LINK FAILURE injected on {e}'); return {'edge':e,'failed':True}
    def restore_link(self,a,b):
        e=key(a,b); r=self.links[e]; r['intf_a'].ifconfig('up'); r['intf_b'].ifconfig('up'); self.forced_failed.discard(e); self._log_event(f'Link restored {e}'); return {'edge':e,'failed':False}
    def _write_csv(self,samples,decision,action):
        stamp=datetime.now(timezone.utc).isoformat(); path='->'.join(self.policy.active_path)
        with open(self.csv_path,'a',newline='') as f:
            w=csv.writer(f)
            for e,s in samples.items(): w.writerow([stamp,self.source,self.destination,'-'.join(e),s['throughput_mbps'],s['capacity_mbps'],s['utilization_pct'],s['queue_packets'],s['queue_bytes'],s['drops_total'],s['drop_delta'],s['loss_pct'],round(edge_cost(s),3),self.last_ping.get('rtt_ms'),self.last_ping.get('loss_pct'),s['congested'],path,decision,action])
    def tick(self):
        with self.lock:
            samples=self._collect(); failed={e for e,s in samples.items() if s['failed']}; congested={e for e,s in samples.items() if s['congested'] and not s['failed']}
            for e in congested-self.previous_congested: self._log_event(f'CONGESTION DETECTED {e}')
            for e in self.previous_congested-congested: self._log_event(f'Congestion cleared {e}')
            self.previous_congested=congested
            candidate=dijkstra(samples,failed,HOST_SWITCH[self.source],HOST_SWITCH[self.destination]); active_cost=self._path_cost(samples,self.policy.active_path) if self.policy.active_path else None; candidate['active_cost']=active_cost
            now=time.monotonic(); switch,reason=self.policy.decide(candidate,failed,now); action='No change'
            if self.auto and switch:
                self._install_path(candidate['path'],self.source,self.destination); self.policy.active_path=candidate['path']; self.policy.last_switch=now; action='SWITCHED to '+'->'.join(candidate['path']); self._log_event(action+' | '+reason)
            elif not self.auto: reason='Automatic switching paused'
            self.last_decision=reason; self.last_action=action
            self.last_metrics={'timestamp':datetime.now(timezone.utc).isoformat(),'edges':samples,'ping':self.last_ping,'candidate':candidate,'active_path':self.policy.active_path,'auto':self.auto,'decision':reason,'action':action,'source':self.source,'destination':self.destination,'source_ip':self.net.get(self.source).IP(),'destination_ip':self.net.get(self.destination).IP(),'traffic_running':bool(self.traffic_process and self.traffic_process.poll() is None)}
            self._write_csv(samples,reason,action)
    def monitor_loop(self):
        self.running=True
        while self.running:
            try: self.tick()
            except Exception as exc: self._log_event('MONITOR ERROR: '+repr(exc)); self.last_decision='Monitor error: '+str(exc)
            time.sleep(self.poll_interval)
    def start_monitor(self): self.thread=threading.Thread(target=self.monitor_loop,daemon=True); self.thread.start()
    def stop(self):
        self.running=False
        if getattr(self,'thread',None) and self.thread.is_alive(): self.thread.join(timeout=3)
        self.stop_traffic(); self._clear_adaptive_flows()
        for sw in SWITCHES: subprocess.run(['ovs-ofctl','-O','OpenFlow13','del-flows',sw],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

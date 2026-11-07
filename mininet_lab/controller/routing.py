"""General graph Dijkstra and adaptive path policy."""
import heapq
from topology.config import EDGES

def key(a,b): return tuple(sorted((a,b)))
CAPACITY = {key(a,b): float(cap) for a,b,cap,_ in EDGES}
BASE_DELAY_MS = {key(a,b): float(delay) for a,b,_,delay in EDGES}

def edge_cost(sample, failed=False):
    if failed: return float('inf')
    cap=max(.1,float(sample.get('capacity_mbps',10)))
    util=min(100.,100.*max(0.,float(sample.get('throughput_mbps',0)))/cap)
    loss=max(0.,float(sample.get('loss_pct',0)))
    queue=max(0.,float(sample.get('queue_packets',0)))
    delay=max(0.,float(sample.get('base_delay_ms',5)))
    return 1.0 + .08*util + 2.0*loss + .35*queue + .10*delay

def dijkstra(samples, failed_edges, source_switch, destination_switch):
    nodes={n for e in CAPACITY for n in e}
    graph={n:[] for n in nodes}
    for edge,cap in CAPACITY.items():
        sample=dict(samples.get(edge,{})); sample.setdefault('capacity_mbps',cap); sample.setdefault('base_delay_ms',BASE_DELAY_MS[edge])
        cost=edge_cost(sample, edge in failed_edges)
        if cost != float('inf'):
            a,b=edge; graph[a].append((b,cost)); graph[b].append((a,cost))
    dist={n:float('inf') for n in nodes}; prev={}; dist[source_switch]=0.; heap=[(0.,source_switch)]
    while heap:
        d,n=heapq.heappop(heap)
        if d != dist[n]: continue
        if n==destination_switch: break
        for nxt,w in graph[n]:
            nd=d+w
            if nd<dist[nxt]: dist[nxt]=nd; prev[nxt]=n; heapq.heappush(heap,(nd,nxt))
    if dist.get(destination_switch,float('inf'))==float('inf'):
        return {'reachable':False,'path':[],'cost':None}
    path=[destination_switch]
    while path[-1]!=source_switch: path.append(prev[path[-1]])
    path.reverse()
    return {'reachable':True,'path':path,'cost':round(dist[destination_switch],3)}

class AdaptivePolicy:
    def __init__(self, improvement=.15, consecutive=3, hold_down=5.):
        self.improvement=improvement; self.consecutive_required=consecutive; self.hold_down=hold_down
        self.active_path=[]; self.better_count=0; self.last_switch=0.
    def uses_failed(self,path,failed): return any(key(path[i],path[i+1]) in failed for i in range(len(path)-1))
    def decide(self,candidate,failed,now):
        if not candidate['reachable']: return False,'No route available'
        if not self.active_path: return True,'Initial route selection'
        if self.uses_failed(self.active_path,failed): return True,'Active path contains failed link; immediate failover'
        if candidate['path']==self.active_path: self.better_count=0; return False,'Current route remains optimal'
        active=candidate.get('active_cost')
        if active is None or active<=0: return False,'Active route cost unavailable'
        self.better_count=self.better_count+1 if candidate['cost']<active*(1-self.improvement) else 0
        if now-self.last_switch<self.hold_down: return False,'Hold-down timer active'
        if self.better_count>=self.consecutive_required:
            self.better_count=0; return True,'Alternative path consistently better'
        return False,f'Waiting for stable improvement ({self.better_count}/{self.consecutive_required})'

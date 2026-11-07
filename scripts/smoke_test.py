#!/usr/bin/env python3
"""Offline tests for the 12-host project's graph and OVS parser."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mininet_lab'))
from controller.routing import dijkstra, key, CAPACITY
from controller.telemetry import parse_ovs_ports

base=dijkstra({},set(),'s1','s5')
assert base['reachable'] and base['path'][0]=='s1' and base['path'][-1]=='s5',base
# Congest a link in the baseline path and verify a valid alternative is computed.
samples={e:{'throughput_mbps':0,'capacity_mbps':c,'loss_pct':0,'queue_packets':0,'base_delay_ms':5} for e,c in CAPACITY.items()}
route0=dijkstra(samples,set(),'s1','s4')
assert route0['reachable'],route0
for e in zip(route0['path'],route0['path'][1:]):
    samples[key(*e)]={'throughput_mbps':1000,'capacity_mbps':1,'loss_pct':10,'queue_packets':500,'base_delay_ms':20}
route1=dijkstra(samples,set(),'s1','s4')
assert route1['reachable'] and route1['path'] != route0['path'],(route0,route1)
failed={key(*e) for e in zip(route0['path'],route0['path'][1:])}
route2=dijkstra({},failed,'s1','s4')
assert route2['reachable'] and route2['path'] != route0['path'],(route0,route2)
assert dijkstra({},set(),'s1','s1')['path']==['s1']
sample_output='''OFPST_PORT reply (OF1.3):\n  port  2: rx pkts=10, bytes=1000, drop=0, errs=0\n           tx pkts=12, bytes=2000, drop=3, errs=0\n  port  3: rx pkts=20, bytes=3000, drop=0, errs=0\n           tx pkts=22, bytes=4000, drop=1, errs=0\n'''
parsed=parse_ovs_ports(sample_output)
assert parsed[2]['tx_bytes']==2000 and parsed[3]['tx_dropped']==1,parsed
print('PASS: multi-switch Dijkstra, alternate route under congestion, failover, same-switch route, OVS counter parser')

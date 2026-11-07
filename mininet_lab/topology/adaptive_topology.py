"""12-PC, 8-switch redundant campus topology."""
from mininet.topo import Topo
from topology.config import HOSTS, HOST_SWITCH, EDGES

class AdaptiveTopo(Topo):
    def build(self):
        for name, ip in HOSTS.items(): self.addHost(name, ip=ip)
        for i in range(1, 9): self.addSwitch(f's{i}', protocols='OpenFlow13', failMode='secure')
        for host, switch in HOST_SWITCH.items(): self.addLink(host, switch)
        for a,b,_cap,delay in EDGES: self.addLink(a,b,delay=f'{delay}ms',bw=100)

topos={'adaptive':AdaptiveTopo}

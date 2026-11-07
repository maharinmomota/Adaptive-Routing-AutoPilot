# Packet Tracer addressing plan

Six separate LANs, each with two PCs and one router gateway:

| LAN | Network | Router gateway | PCs |
|---|---|---|---|
| LAN1 | 192.168.10.0/24 | 192.168.10.1 | .10, .11 |
| LAN2 | 192.168.20.0/24 | 192.168.20.1 | .10, .11 |
| LAN3 | 192.168.30.0/24 | 192.168.30.1 | .10, .11 |
| LAN4 | 192.168.40.0/24 | 192.168.40.1 | .10, .11 |
| LAN5 | 192.168.50.0/24 | 192.168.50.1 | .10, .11 |
| LAN6 | 192.168.60.0/24 | 192.168.60.1 | .10, .11 |

WAN point-to-point links (all /30):

| Link | Network | First endpoint | Second endpoint |
|---|---|---|---|
| R1–R2 | 10.0.12.0/30 | R1 .1 | R2 .2 |
| R2–R3 | 10.0.23.0/30 | R2 .1 | R3 .2 |
| R3–R4 | 10.0.34.0/30 | R3 .1 | R4 .2 |
| R4–R5 | 10.0.45.0/30 | R4 .1 | R5 .2 |
| R5–R6 | 10.0.56.0/30 | R5 .1 | R6 .2 |
| R6–R1 | 10.0.61.0/30 | R6 .2 | R1 .1 |

OSPF process 1, area 0, on all six routers.

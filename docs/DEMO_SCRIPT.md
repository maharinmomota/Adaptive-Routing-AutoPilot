# Suggested live presentation script

1. Introduce the problem: fixed shortest paths can perform poorly when links become congested or fail.
2. Show the Packet Tracer six-router ring with 12 PCs. Explain each LAN and OSPF area 0.
3. Ping PC1A to PC4A. Show `show ip ospf neighbor` and `show ip route 192.168.40.0`.
4. Shut R1–R2 and show OSPF choosing the other side of the ring.
5. Switch to the Ubuntu Mininet dashboard. Select h1 as source and h7 as destination; apply the pair.
6. Start UDP traffic and explain the live link table: throughput, utilization, queue, drops and loss estimate.
7. Apply congestion to an active-path link. Explain the Dijkstra cost formula and observe whether/when the path changes.
8. Fail a link on the active path. Show immediate alternate route installation and ping recovery.
9. Restore the link, select a different PC pair (for example h2 → h10), and repeat a short test.
10. Open `telemetry.csv` and `events.log`; explain how they provide experimental evidence.
11. Conclude: Packet Tracer demonstrates OSPF in a Cisco-style routed network; Mininet demonstrates automated congestion-aware path selection using live Linux/OVS measurements.

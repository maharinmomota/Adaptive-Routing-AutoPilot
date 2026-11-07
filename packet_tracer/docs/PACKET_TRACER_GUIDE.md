# Cisco Packet Tracer — 12 PCs and 6-router OSPF ring

This is the visual Cisco IOS companion lab. Build it in Packet Tracer on Windows. It is a separate simulation from the Ubuntu Mininet controller.

## 1. Devices to add
- 6 × Cisco 2911 routers: R1–R6.
- 6 × 2960 switches: SW1–SW6.
- 12 × PCs: PC1A/PC1B through PC6A/PC6B (two PCs per LAN).
- Copper straight-through for PC-to-switch and switch-to-router connections. Use automatic cable selection or the appropriate copper connection for router-to-router Ethernet.

## 2. Physical layout
Arrange six router/switch/PC groups in a ring:

`LAN1—R1—R2—R3—R4—R5—R6—R1`

Each router has one LAN connection to its local switch and two WAN connections to its clockwise and counter-clockwise neighbor. Each local switch connects its two PCs and its router.

Connections:
- SW1 to R1 G0/0; PC1A and PC1B to SW1.
- R1 G0/1 ↔ R2 G0/1; R1 G0/2 ↔ R6 G0/2.
- SW2 to R2 G0/0; PC2A and PC2B to SW2.
- R2 G0/2 ↔ R3 G0/1.
- SW3 to R3 G0/0; PC3A and PC3B to SW3.
- R3 G0/2 ↔ R4 G0/1.
- SW4 to R4 G0/0; PC4A and PC4B to SW4.
- R4 G0/2 ↔ R5 G0/1.
- SW5 to R5 G0/0; PC5A and PC5B to SW5.
- R5 G0/2 ↔ R6 G0/1.
- SW6 to R6 G0/0; PC6A and PC6B to SW6.

If the router model has different interface names, use the interface names shown in its Config/CLI tab and adjust the config files accordingly. Confirm each cable link turns green after interfaces are configured.

## 3. Configure the 12 PCs
On each PC: Desktop → IP Configuration → Static. Use:

| PC | IP address | Mask | Default gateway |
|---|---|---|---|
| PC1A | 192.168.10.10 | 255.255.255.0 | 192.168.10.1 |
| PC1B | 192.168.10.11 | 255.255.255.0 | 192.168.10.1 |
| PC2A | 192.168.20.10 | 255.255.255.0 | 192.168.20.1 |
| PC2B | 192.168.20.11 | 255.255.255.0 | 192.168.20.1 |
| PC3A | 192.168.30.10 | 255.255.255.0 | 192.168.30.1 |
| PC3B | 192.168.30.11 | 255.255.255.0 | 192.168.30.1 |
| PC4A | 192.168.40.10 | 255.255.255.0 | 192.168.40.1 |
| PC4B | 192.168.40.11 | 255.255.255.0 | 192.168.40.1 |
| PC5A | 192.168.50.10 | 255.255.255.0 | 192.168.50.1 |
| PC5B | 192.168.50.11 | 255.255.255.0 | 192.168.50.1 |
| PC6A | 192.168.60.10 | 255.255.255.0 | 192.168.60.1 |
| PC6B | 192.168.60.11 | 255.255.255.0 | 192.168.60.1 |

## 4. Configure routers
Open each router → CLI. Answer `no` to the initial configuration dialog if it appears. Copy/paste the corresponding full file from `packet_tracer/configs/R1.txt` through `R6.txt` into that router's CLI. The configs enable all interfaces, assign the LAN/WAN addresses, and advertise directly connected networks in OSPF area 0.

Wait 30–60 seconds for OSPF neighbors and routes to converge.

## 5. Verify connectivity
From PC1A → Desktop → Command Prompt:

```text
ping 192.168.40.10
ping 192.168.60.10
```

Try PC2B to PC5A too. On each router CLI:

```text
show ip interface brief
show ip ospf neighbor
show ip route ospf
show ip route 192.168.50.0
```

The OSPF neighbor table should show the two adjacent routers. The routing table should contain remote LAN routes.

## 6. Demonstrate path selection and failover
1. Select PC1A as source and PC4A as destination. Run continuous ping from the PC command prompt if supported, or repeat ping.
2. On R1, inspect `show ip route 192.168.40.0` and `show ip ospf neighbor`.
3. Disable the R1-to-R2 interface:

```text
enable
configure terminal
interface gigabitEthernet0/1
shutdown
end
```

4. Wait for OSPF convergence. The route to LAN4 should use the other side of the ring through R6/R5/R4.
5. Verify with `show ip route 192.168.40.0`; repeat ping. The first one or two pings may time out while OSPF converges.
6. Restore the interface:

```text
configure terminal
interface gigabitEthernet0/1
no shutdown
end
```

7. To show a deliberate OSPF metric preference rather than a failure, set a higher cost on R1's clockwise interface and compare routes:

```text
configure terminal
interface gigabitEthernet0/1
ip ospf cost 100
end
show ip route 192.168.40.0
```

Restore a lower cost with `no ip ospf cost` or a value you choose, then inspect the route again.

## 7. Packet Tracer Simulation Mode
1. Switch from Realtime to Simulation.
2. Use Add Simple PDU (envelope icon), click PC1A, then PC4A.
3. Press Capture/Forward to inspect packet traversal through switches and routers.
4. Repeat after shutting down R1–R2. The packet should traverse the other side of the ring after routing converges.

## 8. Save and collect project evidence
- Save the `.pkt` file in your project folder.
- Take a screenshot of the full six-router topology with all 12 PCs.
- Take screenshots of successful pings before and after failure.
- Capture `show ip ospf neighbor` and `show ip route` output on at least R1 and R4.
- Include a short table showing source PC, destination PC, chosen route, event (normal/failure), and result.

## 9. Important distinction
Packet Tracer's OSPF ring shows Cisco dynamic routing and link-state convergence. The dashboard's live throughput/queue/drop measurements and automatic Dijkstra-based OpenFlow steering run in the Ubuntu Mininet lab. Use both as complementary demonstrations; do not claim Packet Tracer telemetry is controlling Mininet.

# Adaptive Routing Algorithms in Computer Networks — AutoPilot v4

**Expanded multi-PC edition:** 12 selectable PCs, 8 Open vSwitches, 14 redundant backbone links, live telemetry, Dijkstra route selection, congestion-aware adaptation and immediate link-failure failover.

## What you can demonstrate
- Select any source PC and destination PC (`h1`–`h12`) from the browser dashboard.
- Generate TCP or UDP traffic between that exact pair.
- Inspect measured throughput, utilization, queue backlog, drops, estimated link loss, end-to-end ping RTT and packet loss.
- Inject congestion on any backbone link, clear it, fail a link, and restore it.
- Let the controller compare path costs using Dijkstra and install forward/reverse OpenFlow rules for the selected pair.
- Export evidence from `mininet_lab/logs/telemetry.csv` and `events.log`.

## Environments
1. **Windows:** VirtualBox/VMware, Cisco Packet Tracer, browser and project files.
2. **Packet Tracer:** six Cisco 2911 routers in a ring, six access switches and 12 PCs (two PCs per LAN) using OSPF.
3. **Ubuntu VM:** Mininet, Open vSwitch, Python/Flask, iperf3 and Linux `tc`; this runs the automated 12-host controller and dashboard.

Packet Tracer and Mininet are complementary demonstrations. The Mininet controller does not directly control the separate Packet Tracer simulation.

## Start in this order
1. Read `docs/WINDOWS_UBUNTU_SETUP.md` completely.
2. Build the six-router, 12-PC Packet Tracer topology using `packet_tracer/docs/PACKET_TRACER_GUIDE.md` and `packet_tracer/configs/R1.txt`–`R6.txt`.
3. In Ubuntu, install Mininet/OVS/iperf3/Flask as described in the setup guide.
4. Run `cd mininet_lab && sudo python3 run_lab.py`.
5. Open `http://<Ubuntu-host-only-IP>:5000` in Windows.
6. Select source/destination PCs, start traffic, inject congestion, fail/restore links and save the CSV evidence.

## Main folders
- `mininet_lab/topology/adaptive_topology.py`: 12 hosts, host-to-switch mapping and 8-switch/14-link backbone.
- `mininet_lab/controller/routing.py`: generalized Dijkstra and hysteresis policy.
- `mininet_lab/controller/lab_controller.py`: pair selection, traffic generation, telemetry, OpenFlow path steering and event/CSV logs.
- `mininet_lab/controller/dashboard.py`: source/destination selector and live control dashboard.
- `packet_tracer/configs/`: six Cisco IOS OSPF configurations.
- `docs/`: detailed Windows/Ubuntu installation, algorithm, demo and evaluation guide.
- `scripts/smoke_test.py`: offline routing/parser test (does not require Mininet).

## Requirements
Windows 10/11, 8 GB RAM minimum (16 GB recommended), virtualization enabled, VirtualBox/VMware, Ubuntu 22.04 LTS VM, Cisco Packet Tracer, Mininet, Open vSwitch, iperf3, iproute2, Python 3 and Flask.

**Validation note:** source syntax and offline routing tests can be checked on the build machine, but the live OVS/Mininet lab must be run and validated inside your Ubuntu VM.

# Adaptive Routing AutoPilot v4

**An intelligent adaptive routing framework using Software-Defined Networking (SDN), Mininet, Open vSwitch, and Dijkstra's shortest-path algorithm.**

## Overview

Adaptive Routing AutoPilot is a computer networking research project designed to improve network path selection through real-time telemetry monitoring and adaptive routing.

The system uses a Python-based controller to monitor network conditions, calculate dynamic link costs, detect congestion, and automatically select alternative paths when network conditions change.

It also includes a separate Cisco Packet Tracer implementation demonstrating OSPF-based dynamic routing and network convergence.

## Key Features

- Multi-host network topology with 12 virtual PCs.
- Real-time network telemetry monitoring.
- Dijkstra-based adaptive path selection.
- Congestion-aware routing optimization.
- Automatic link-failure detection and recovery.
- OpenFlow 1.3-based forwarding rule installation.
- Flask-based network monitoring dashboard.
- Throughput, latency, packet loss, and link utilization analysis.
- CSV-based experimental data logging.
- Cisco OSPF routing demonstration in Packet Tracer.

## Technologies Used

- Python
- Mininet
- Open vSwitch (OVS)
- Software-Defined Networking (SDN)
- OpenFlow 1.3
- Dijkstra's Algorithm
- Flask
- Linux Traffic Control (`tc`)
- iperf3
- Cisco Packet Tracer
- OSPF

## Project Structure

```text
Adaptive_Routing_AutoPilot_v4/
├── docs/
├── mininet_lab/
│   ├── topology/
│   ├── controller/
│   ├── logs/
│   └── run_lab.py
├── packet_tracer/
│   ├── configs/
│   └── docs/
└── scripts/
```

## Requirements

- Windows 10/11
- VirtualBox or VMware
- Ubuntu 22.04 LTS
- Python 3
- Mininet
- Open vSwitch
- Flask
- iperf3
- Cisco Packet Tracer (for the OSPF demonstration)

## Installation & Execution

Install the required dependencies in Ubuntu:

```bash
sudo apt update

sudo apt install -y mininet openvswitch-switch iperf3 \
iproute2 iputils-ping python3 python3-flask
```

Start Open vSwitch:

```bash
sudo systemctl enable --now openvswitch-switch
```

Navigate to the project directory:

```bash
cd mininet_lab
```

Launch the adaptive routing environment:

```bash
sudo python3 run_lab.py
```

Access the Flask dashboard:

```text
http://<UBUNTU-VM-IP>:5000
```

Replace `<UBUNTU-VM-IP>` with your Ubuntu virtual machine's reachable IP address.

## Experimental Scenarios

The project supports the following network experiments:

1. **Baseline Connectivity:** Evaluate communication between selected hosts.
2. **Multi-Host Routing:** Test adaptive routing across different source-destination pairs.
3. **Congestion Management:** Introduce network congestion and observe alternative path selection.
4. **Link Failure Recovery:** Simulate backbone link failures and evaluate automatic route recovery.
5. **OSPF Convergence:** Demonstrate dynamic routing behavior using Cisco Packet Tracer.

## Performance Evaluation

The system records network performance metrics, including:

- Throughput (Mbps)
- Round-Trip Time (RTT)
- Packet Loss (%)
- Link Utilization (%)
- Queue Backlog
- Routing Cost
- Route Switching Time
- Link Failure Recovery Time

Experimental measurements are stored in:

```text
mininet_lab/logs/
```

- `telemetry.csv` — Network performance and telemetry data.
- `events.log` — Routing decisions and network events.

## Testing

Run the offline smoke test from the project root:

```bash
python3 scripts/smoke_test.py
```

This validates selected routing algorithms and telemetry parsing functionality.

## Research Contribution

This project is informed by existing research on adaptive routing and Software-Defined Networking. It explores the application of telemetry-driven link-cost estimation and dynamic path selection in a Mininet/Open vSwitch environment.

The implementation also provides a separate OSPF-based network simulation for comparative educational demonstration.

**Note:** The original research paper should be properly cited here before academic publication or submission.

## Future Improvements

- Advanced congestion prediction.
- Machine learning-based routing optimization.
- Improved telemetry analysis.
- Large-scale network performance evaluation.
- Enhanced routing stability and failover mechanisms.

## Acknowledgement

Developed as an academic computer networking research project to explore adaptive routing, network optimization, and Software-Defined Networking concepts.

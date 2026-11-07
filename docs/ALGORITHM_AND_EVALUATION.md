# Algorithm and evaluation plan

## Network model
The Mininet experiment has 12 hosts on four access switches (three hosts each) and an eight-switch redundant backbone. Backbone edges are configured with capacity and baseline delay metadata. The controller measures live OVS port-counter deltas and Linux qdisc backlog/drop counters.

## Dijkstra link cost
For each link:

`C = 1 + 0.08U + 2L + 0.35Q + 0.10D`

- `U`: measured utilization percentage, capped at 100.
- `L`: estimated link loss percentage.
- `Q`: current qdisc backlog in packets.
- `D`: configured baseline delay in milliseconds.
- Failed links are assigned infinite cost and excluded from the graph.

Dijkstra computes a minimum-cost switch path between the switch connected to the selected source PC and the switch connected to the selected destination PC. The controller installs matching forward and reverse IPv4 flows along that path.

## Stability and failover
For congestion-driven changes, the alternative must be at least 15% cheaper for three consecutive samples, with a five-second hold-down. If a link in the active path fails, failover is immediate (provided an alternate route exists). This avoids route oscillation while prioritizing recovery from failures.

## Measurements
- Throughput: sum of transmit-byte counter deltas at both ends of a backbone link divided by elapsed polling time.
- Queue: instantaneous Linux qdisc backlog packet and byte counts at both link endpoints.
- Drops: qdisc drop-counter deltas plus OVS transmit-drop deltas.
- Link loss estimate: observed drops divided by observed transmitted packet count plus drops. This is a controller-side estimate, not a hardware PHY measurement.
- End-to-end RTT and packet loss: ICMP ping from the selected source host to the selected destination host.

## Evaluation matrix

| Test | Source/destination | Event | Expected observation |
|---|---|---|---|
| Baseline | h1 → h7 | No impairment | Stable path, low queues/drops, successful ping |
| Pair change | h2 → h10 | Select a new pair | Controller installs a path for the newly selected PCs |
| Congestion | h1 → h7 | Rate-limit one active-path link | Higher utilization/queue/drop and a better alternate path may be selected |
| Failure | h1 → h7 | Shut an active-path link | Immediate route recomputation around the failed link |
| Recovery | h1 → h7 | Restore link | Link returns to graph; controller may keep current route unless a better route is stable |
| Multi-pair | h4 → h12, h3 → h8, h11 → h1 | Repeat baseline and impairment | Demonstrate that pair selection is not hard-coded to one PC pair |

## Results to include in report
Record each selected PC pair, baseline path, impaired link, congestion settings, route before/after, average RTT, ping loss, peak utilization, maximum queue backlog, drop delta and recovery time. Plot throughput and RTT over time from the CSV. State that Packet Tracer demonstrates Cisco OSPF convergence while Mininet provides measured telemetry and controller-driven OpenFlow route installation.

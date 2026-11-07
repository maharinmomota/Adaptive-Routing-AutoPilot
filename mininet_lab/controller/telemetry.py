"""Real-time telemetry from OVS counters, Linux qdisc and host ping."""
import re
import subprocess
import time

def run(cmd, timeout=5):
    p = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout

def parse_ovs_ports(text):
    """Return {port_no: {'tx_bytes':..., 'tx_packets':..., 'tx_dropped':...}}."""
    result = {}
    # ovs-ofctl commonly prints rx and tx counters on separate lines per port.
    blocks = re.split(r"(?=\bport\s+\d+:)", text)
    for block in blocks:
        pm = re.search(r"\bport\s+(\d+):", block)
        tm = re.search(r"tx\s+pkts=(\d+),\s*bytes=(\d+),\s*drop=(\d+)", block, re.S)
        if pm and tm:
            result[int(pm.group(1))] = {
                "tx_packets": int(tm.group(1)),
                "tx_bytes": int(tm.group(2)),
                "tx_dropped": int(tm.group(3)),
            }
    return result

def get_ovs_port_stats(switch):
    _, out = run(f"ovs-ofctl -O OpenFlow13 dump-ports {switch}")
    return parse_ovs_ports(out)

def get_qdisc_stats(interface):
    _, out = run(f"tc -s qdisc show dev {interface}")
    backlog_bytes = backlog_packets = drops = 0
    m = re.search(r"backlog\s+(\d+)b\s+(\d+)p", out)
    if m:
        backlog_bytes, backlog_packets = int(m.group(1)), int(m.group(2))
    # tc output may show dropped X, overlimits Y, requeues Z
    m = re.search(r"dropped\s+(\d+)", out)
    if m:
        drops = int(m.group(1))
    return {"backlog_bytes": backlog_bytes, "backlog_packets": backlog_packets,
            "drops_total": drops, "raw": out.strip()}

def get_ping_metrics(host, destination="10.0.0.2", count=3):
    out = host.cmd(f"ping -n -c {count} -W 1 {destination}")
    sent = received = 0
    loss = 100.0
    avg_rtt = None
    m = re.search(r"(\d+) packets transmitted,\s*(\d+) (?:packets )?received,\s*([\d.]+)% packet loss", out)
    if m:
        sent, received, loss = int(m.group(1)), int(m.group(2)), float(m.group(3))
    m = re.search(r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = [\d.]+/([\d.]+)/", out)
    if m:
        avg_rtt = float(m.group(1))
    return {"sent": sent, "received": received, "loss_pct": loss,
            "rtt_ms": avg_rtt, "raw": out.strip()}

def parse_iperf_receiver_mbps(json_text):
    import json
    try:
        data = json.loads(json_text)
        end = data.get("end", {})
        summary = end.get("sum_received") or end.get("sum") or {}
        return round(float(summary.get("bits_per_second", 0)) / 1_000_000, 3)
    except Exception:
        return None

# Complete setup guide — Windows host + Ubuntu Mininet VM

This project is intentionally split into two environments. Packet Tracer demonstrates Cisco routers and OSPF visually. Ubuntu/Mininet runs the automated experiment with real Linux traffic counters, queues, drops, Dijkstra and OpenFlow route installation. The Packet Tracer simulation does not feed telemetry into the Mininet controller.

## 1. Hardware and software checklist

### Recommended computer
- Windows 10/11, 64-bit.
- 8 GB RAM minimum; 16 GB recommended.
- 25 GB free disk space for the VM and project.
- Intel/AMD processor with hardware virtualization enabled (Intel VT-x or AMD-V).
- Internet access for downloads and package installation.

### Install on Windows
1. Check Windows Task Manager → Performance → CPU → Virtualization. It should say Enabled. If it says Disabled, enable Intel VT-x/AMD-V in your computer BIOS/UEFI, then restart Windows.
2. Install **Oracle VirtualBox** from https://www.virtualbox.org/wiki/Downloads (or VMware Workstation from its official site).
3. Download the **Ubuntu 22.04 LTS Desktop ISO** from https://ubuntu.com/download/desktop.
4. Install **Cisco Packet Tracer**: open Cisco’s official Resource Hub at https://www.netacad.com/resources/lab-downloads, sign in or create a free Cisco/Skills for All account, download the Windows 64-bit installer, run it, accept the license and keep the default installation options unless you have a reason to change them. On first launch, complete the Skills for All sign-in prompt. The exact current installer/version is shown by Cisco in the Resource Hub.
5. Optional but useful: install **7-Zip** to extract the project ZIP, and **Visual Studio Code** to inspect Python/config files.
6. Extract `Adaptive_Routing_AutoPilot_v4_Multi_PC.zip` into a simple folder such as `C:\Networks\Adaptive_Routing_AutoPilot_v4`.

## 2. Create the Ubuntu virtual machine

1. Open VirtualBox → New.
2. Name: `Ubuntu-Mininet-Lab`; Type: Linux; Version: Ubuntu (64-bit).
3. Memory: 4096 MB minimum; 6144–8192 MB recommended if your PC has 16 GB RAM.
4. CPUs: 2 minimum, 4 recommended.
5. Create a dynamically allocated virtual disk, 25–35 GB.
6. Settings → Storage → attach the Ubuntu ISO to the virtual optical drive.
7. Settings → Network → Adapter 1: **NAT** (internet access).
8. Settings → Network → Adapter 2: enable **Host-only Adapter** (Windows browser access to dashboard). If VirtualBox has no host-only network yet, open Tools → Network → Host-only Networks → Create.
9. Start the VM and install Ubuntu. Choose normal installation; create a username/password you can remember. Reboot and eject the ISO when asked.
10. In Ubuntu, open Terminal. Update Ubuntu:

```bash
sudo apt update && sudo apt upgrade -y
```

11. Check both network adapters:

```bash
ip -br address
```

You should see an internet/NAT interface and a host-only interface. The host-only address is normally a private address such as `192.168.56.x`; use the actual address shown on your VM.

## 3. Install Mininet and supporting packages in Ubuntu

Run these commands in the **Ubuntu VM terminal**, not Windows PowerShell:

```bash
sudo apt update
sudo apt install -y mininet openvswitch-switch iperf3 iproute2 iputils-ping python3 python3-flask python3-pip git curl
sudo systemctl enable --now openvswitch-switch
```

Check installations:

```bash
mn --version
ovs-vsctl --version
iperf3 --version
python3 --version
```

Test Mininet before running the project:

```bash
sudo mn --switch ovsbr --test pingall
```

The test should finish with `0% dropped`. Clean up afterward:

```bash
sudo mn -c
```

If the Ubuntu package version is too old or `mn` is missing, follow the official Mininet installation page at https://mininet.org/download/ and use its Ubuntu/source instructions. Do not run two Mininet labs at the same time.

## 4. Copy the project into Ubuntu

Easy method:
1. In VirtualBox, install Guest Additions if you want shared folders, then configure a shared folder from Windows.
2. Alternatively, use a USB/shared folder, or download/copy the ZIP into Ubuntu.
3. Extract it in Ubuntu (right-click → Extract Here), or use:

```bash
mkdir -p ~/projects
cd ~/projects
unzip ~/Downloads/Adaptive_Routing_AutoPilot_v4_Multi_PC.zip
```

Your project directory should contain `README.md`, `mininet_lab/`, `packet_tracer/`, `docs/`, and `scripts/`.

If using a Windows shared folder, copy the extracted folder into Ubuntu's home directory before running. Do not run Mininet directly from a mounted Windows/NTFS shared folder; use a normal Linux ext4 folder.

## 5. Install/check Python dependencies

The controller uses Flask. Ubuntu's apt-installed Flask is the simplest option and avoids Python's externally-managed-environment restriction. Confirm:

```bash
python3 -c "import flask; print('Flask', flask.__version__)"
```

If Flask is missing, run:

```bash
sudo apt install -y python3-flask
```

## 6. Start the 12-PC Mininet lab

In Ubuntu Terminal:

```bash
cd ~/projects/Adaptive_Routing_AutoPilot_v4/mininet_lab
sudo python3 run_lab.py
```

Keep this terminal open. Mininet will create 12 virtual PCs (`h1`–`h12`), 8 Open vSwitch switches (`s1`–`s8`) and 14 inter-switch links. The dashboard will listen on port 5000.

Find the Ubuntu host-only IP in a second Ubuntu terminal:

```bash
ip -4 -br address
```

On Windows, open Chrome/Edge and enter:

```text
http://<UBUNTU-HOST-ONLY-IP>:5000
```

Example only: `http://192.168.56.101:5000`. Use the address shown on your VM, not the example. If Windows cannot open it, check that Adapter 2 is Host-only, that the address belongs to that adapter, and that Ubuntu's firewall allows TCP port 5000. You can test locally inside Ubuntu with `curl http://127.0.0.1:5000`.

## 7. Select any source and destination PC

The dashboard has two dropdowns. Select any different pair from `h1` through `h12` and click **Apply PC pair**. Each host is assigned a fixed address in `10.10.0.0/24`:

| PC | IPv4 address | Attached switch |
|---|---|---|
| h1 | 10.10.0.1 | s1 |
| h2 | 10.10.0.2 | s1 |
| h3 | 10.10.0.3 | s1 |
| h4 | 10.10.0.4 | s4 |
| h5 | 10.10.0.5 | s4 |
| h6 | 10.10.0.6 | s4 |
| h7 | 10.10.0.7 | s5 |
| h8 | 10.10.0.8 | s5 |
| h9 | 10.10.0.9 | s5 |
| h10 | 10.10.0.10 | s6 |
| h11 | 10.10.0.11 | s6 |
| h12 | 10.10.0.12 | s6 |

The dashboard installs host-pair-specific forward and reverse OpenFlow rules along the selected switch path. Select a new pair whenever you want to run a different source/destination experiment.

## 8. Recommended experiment procedure

### Experiment A — baseline connectivity
1. Start the lab and open the dashboard.
2. Choose `h1` as source and `h7` as destination; click Apply PC pair.
3. Wait 3–5 seconds for the first measurements.
4. Start UDP 25 Mbps traffic.
5. Watch active route, RTT, packet loss and the link table.
6. Stop traffic after recording baseline results.

### Experiment B — congestion-aware route selection
1. Select a pair whose route uses `s1-s2-s4-s5` or another backbone path; check the Active route.
2. Start UDP traffic at 25 Mbps.
3. In the link dropdown, choose a link that is on the active path (for example `s1-s2` if the path includes it).
4. Apply congestion: 3 Mbps, 80 ms delay, 1% loss.
5. Wait for telemetry and the controller's hysteresis (up to a few seconds). Observe congestion state and route changes.
6. Clear congestion on that same link.
7. Record before/after route, RTT, utilization, queue, drops and loss.

### Experiment C — link failure and recovery
1. Select a pair with at least two available routes; start traffic.
2. Select a link that appears in the active path and click **Fail link**.
3. The controller excludes the failed edge and should immediately install an alternative route if one exists.
4. Confirm ping resumes and the active route no longer includes the failed link.
5. Click **Restore link**. The controller may remain on the current path until the alternative is consistently better.

### Experiment D — change the PC pair
1. Stop current traffic.
2. Select `h2` → `h10`, apply the pair, and repeat baseline.
3. Try `h4` → `h12`, `h3` → `h8`, `h11` → `h1`.
4. Include at least four source/destination pairs in your report.

## 9. Files generated and evidence to collect

In `mininet_lab/logs/`:
- `telemetry.csv`: one row per measured backbone link per polling interval, including source/destination, throughput, utilization, queue, drops, estimated loss, edge cost, RTT, ping loss, congestion, active path and controller decision.
- `events.log`: timestamped congestion detection, congestion clearing, route installation, link failure/recovery and route-switch events.

Open `telemetry.csv` with Excel. Filter by source and destination. Take screenshots of the dashboard before congestion, during congestion, after reroute, during link failure and after recovery. Include the CSV graphs/tables in the final report.

## 10. Shut down safely

1. Stop traffic from the dashboard.
2. Return to the Ubuntu terminal running the lab and press `Ctrl+C` once.
3. If Mininet does not clean up, open another terminal and run:

```bash
sudo mn -c
```

4. Shut down Ubuntu normally, then close VirtualBox.

## 11. Common problems

- **`ModuleNotFoundError: No module named mininet`:** run in Ubuntu, install `mininet`, and verify `mn --version`. Do not run this Python script in Windows.
- **Open vSwitch not running:** `sudo systemctl restart openvswitch-switch`; then `sudo mn -c` and retry.
- **`iperf3: command not found`:** `sudo apt install -y iperf3`.
- **Dashboard not reachable from Windows:** use the host-only adapter IP, not the NAT IP; check `ip -4 -br address`; try `curl http://127.0.0.1:5000` inside Ubuntu.
- **No traffic / no route:** reselect source and destination, make sure they differ, start traffic, and wait a few seconds. Try a simple host ping in the Mininet CLI only if you add a CLI to the launcher; otherwise inspect `events.log` and terminal errors.
- **A link stays congested after clearing:** click Clear congestion on the same edge and allow a few measurement intervals for counters/queues to settle.
- **No alternate route after failure:** you may have failed a bridge link that disconnects one of the endpoint access switches, or selected a pair with no remaining graph path. Restore the link and try a different edge.
- **Run as root:** the lab must be launched with `sudo` because Mininet, namespaces, `tc`, and Open vSwitch need elevated privileges.
- **Do not run two copies:** stop the current lab and run `sudo mn -c` before restarting.

## 12. What each environment is responsible for

| Environment | Use it for | Do not expect it to do |
|---|---|---|
| Windows | Install tools, open dashboard, edit/report files | Run Linux Mininet/OVS directly |
| Cisco Packet Tracer | Draw and simulate Cisco routers, OSPF, multiple PCs, ping, link/cost changes | Provide the live OVS qdisc telemetry used by the Python controller |
| Ubuntu VM | Run Mininet, OVS, Python controller, iperf3, tc, telemetry and automatic route switching | Run the Packet Tracer GUI |

Official Mininet install guidance: https://mininet.org/download/ and walkthrough: https://mininet.org/walkthrough/.

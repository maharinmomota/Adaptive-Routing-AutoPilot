#!/usr/bin/env python3
"""Launch the Mininet network, continuous adaptive controller and web dashboard."""
import os, sys, time, threading, signal
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from topology.adaptive_topology import AdaptiveTopo
from controller.lab_controller import LabController
from controller.dashboard import create_app

def main():
    if os.geteuid() != 0:
        print("Run as root: sudo python3 run_lab.py")
        sys.exit(1)
    setLogLevel("info")
    net = Mininet(topo=AdaptiveTopo(), switch=OVSSwitch, controller=None, link=TCLink,
                  autoSetMacs=True, build=True)
    info("*** Starting OVS switches and hosts\n")
    net.start()
    controller = None
    try:
        controller = LabController(net, poll_interval=1.0)
        controller.start_monitor()
        app = create_app(controller)
        info("*** Dashboard: http://<Ubuntu-VM-IP>:5000\n")
        info("*** Start traffic and run congestion/failure experiments from the dashboard.\n")
        app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        if controller:
            controller.stop()
        info("*** Stopping Mininet\n")
        net.stop()

if __name__ == "__main__":
    main()

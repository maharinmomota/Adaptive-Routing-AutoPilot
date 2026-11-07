#!/usr/bin/env bash
set -e
echo "Python:"; python3 --version
echo "Mininet:"; mn --version
echo "Open vSwitch:"; ovs-vsctl --version | head -1
echo "iperf3:"; iperf3 --version | head -1
echo "Flask:"; python3 -c 'import flask; print(flask.__version__)'

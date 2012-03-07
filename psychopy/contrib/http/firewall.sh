#!/bin/bash

# UNTESTED - run as root, won't survive reboot

# --- firewall: drop incoming connections if IP make more than 10 connection attempts to port 80 within 100 seconds

IPT=/sbin/iptables
# Max connection in seconds
SECONDS=100
# Max connections per IP
BLOCKCOUNT=10
# default action can be DROP or REJECT
DACTION="DROP"
$IPT -A INPUT -p tcp --dport 80 -i eth0 -m state --state NEW -m recent --set
$IPT -A INPUT -p tcp --dport 80 -i eth0 -m state --state NEW -m recent --update --seconds ${SECONDS} --hitcount ${BLOCKCOUNT} -j ${DACTION}

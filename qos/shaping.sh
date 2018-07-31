#!/opt/bin/bash

#USAGE: netspeed -u limit -d limit | -s
usage="$(basename "$0") -l speed_limit | -s
  -u speed_limit: upload speed limit with units (eg. 1mbit, 100kbit)
  -d speed_limit: download speed limit with units (eg. 1mbit, 100kbit)
  -s: remove all limits
"

TC=/bin/tc

# default values
DL=9500kbit
DL2=2000kbit
UL=950kbit
UL2=200kbit
STOP=0

# hardcoded constats
IFACE=ifb0 # fake interface to shape ingress traffic
WAN=eth3 # interface which in connected to the internet

while getopts ':hu:d:s' option; do
 case "$option" in
  u) UL=$OPTARG
   debug "Upload limit: $UL"
   ;;
  d) DL=$OPTARG
   debug "Download limit: $DL"
   ;;
  s) STOP=1
   ;;
  h) echo "$usage"
   exit
   ;;
 esac
done

function limitExists { # detected by ingress on $WAN qdisc
 # -n equals true if non-zero string length
 if [[ -n `tc qdisc show | grep "ingress .* $WAN"` ]]
 then
  return 0
 else
  return 1
 fi
}

function ifaceExists {
 # -n equals true if non-zero string length
 if [[ -n `ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d' | \
  grep $IFACE` ]]
 then
  return 0
 else
  return 1
 fi
}

function ifaceIsUp {
 # -n equals true if non-zero string length
 if [[ -n `ifconfig | sed 's/[ \t].*//;/^\(lo\|\)$/d' | grep $IFACE` ]]
 then
  return 0
 else
  return 1
 fi
}

function createIFB {
 # Loading modules ifb
 if [ -z "$(lsmod | grep ifb)" ]; then
  debug "Loading IFB device"
  modprobe ifb numifbs=1
  ip link set dev ifb0 up
 fi

 if ! ifaceIsUp; then
  debug "Enabling IFB device"
  ip link set dev ifb0 up
 fi
}

function limitUpload {
 log "Setting upload limit: $UL"

 # Set the new root handle, the default traffic will be in class 1:90 (lowest priority)
 $TC qdisc add dev $WAN root handle 1: htb default 90

 # Set the width of the channel through the uppermost class
 $TC class add dev $WAN parent 1: classid 1:1 \
  htb rate $UL ceil $UL burst 6k

 # Classes and their priorities: three classes:
 #  1:10 - high priority
 #  1:50 - medium priority
 #  1:90 - low priority
 $TC class add dev $WAN parent 1:1 classid 1:10 \
  htb rate 5kbit ceil $UL \
  burst 6k prio 1
 $TC class add dev $WAN parent 1:1 classid 1:50 \
  htb rate $UL2 ceil $UL \
  burst 6k prio 2
 $TC class add dev $WAN parent 1:1 classid 1:90 \
  htb rate $UL2 ceil $UL \
  prio 3

 $TC qdisc add dev $WAN parent 1:10 handle 10: sfq perturb 10
 $TC qdisc add dev $WAN parent 1:50 handle 50: sfq perturb 10
 $TC qdisc add dev $WAN parent 1:90 handle 90: sfq perturb 10

 # Define filters that distribute different services by class.
 ### HIGH PRIO

 # ICMP
 $TC filter add dev $WAN parent 1: protocol ip prio 1 u32 \
  match ip protocol 1 0xff \
  flowid 1:10

 # ACK
 $TC filter add dev $WAN parent 1: protocol ip prio 1 u32 \
  match ip protocol 6 0xff \
  match u8 0x05 0x0f at 0 \
  match u16 0x0000 0xffc0 at 2 \
  match u8 0x10 0xff at 33 \
  flowid 1:10

 # DNS
 $TC filter add dev $WAN parent 1: protocol ip prio 1 u32 \
  match ip protocol 17 0xff \
  match ip sport 53 0xffff \
  flowid 1:10

 # VOIP
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip tos 0x68 0xff \
  match ip protocol 11 0xff \
  flowid 1:10
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip tos 0xb8 0xff \
  match ip protocol 11 0xff \
  flowid 1:10

 # TOS
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip tos 0x10 0xff \
  flowid 1:10

 # SSH + TELNET
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip protocol 6 0xff \
  match ip sport 22 0xfffe \
  flowid 1:10

 # RDP
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip protocol 6 0xff \
  match ip sport 3389 0xffff \
  flowid 1:10

 # NTP
 $TC filter add dev $WAN parent 1: protocol ip prio 2 u32 \
  match ip protocol 17 0xff \
  match ip sport 123 0xffff \
  flowid 1:10

 ### MED PRIO
 # SMTP
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 25 0xffff \
  flowid 1:50
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 465 0xffff \
  flowid 1:50
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 587 0xffff \
  flowid 1:50

 # IMAP
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 143 0xffff \
  flowid 1:50
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 993 0xffff \
  flowid 1:50

 # HTTPS
 $TC filter add dev $WAN parent 1: protocol ip prio 5 u32 \
  match ip protocol 6 0xff \
  match ip sport 443 0xffff \
  flowid 1:50

 # WWW
 $TC filter add dev $WAN parent 1: protocol ip prio 6 u32 \
  match ip protocol 6 0xff \
  match ip sport 80 0xffff \
  flowid 1:50

 ### LOW PRIO Default
 # All other stuff
}

function limitDownload {
 if ! ifaceIsUp; then
  debug "IFB device not running."
  return
 fi

 log "Setting download limit: $DL"

 # redirect ingress
 $TC qdisc add dev $WAN handle ffff: ingress
 $TC filter add dev $WAN parent ffff: protocol ip u32 \
  match u32 0 0 action mirred egress redirect dev $IFACE

 # add ingress rules to virtual interface
 $TC qdisc add dev $IFACE root handle 1: htb default 10
 $TC class add dev $IFACE parent 1: classid 1:1 htb rate $DL ceil $DL
 $TC class add dev $IFACE parent 1:1 classid 1:10 htb rate $DL ceil $DL
}

function removeLimits {
 if limitExists ; then
  debug "Removing QoS rules"
  $TC qdisc del dev $WAN ingress
  $TC qdisc del dev $WAN root
  $TC qdisc del dev $IFACE root
 fi
 if ifaceIsUp ; then
  debug "Shutdown IFB device"
  ip link set dev $IFACE down
 fi
}

#
# main script
#
if [ $STOP -eq 1 ]; then
 removeLimits
 exit 0
fi

if [ "$DL" != "0" ]; then
 # always remove existing before setting new
 removeLimits

 # prepare interface
 createIFB

 # set limits
 limitUpload
 limitDownload
fi

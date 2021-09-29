#!/bin/bash

show_help()
{
  echo "share_internet.sh interface subnet

This is a simple script that forwards a linux computer's internet to a \
second subnet
the method for this script came from: https://medium.com/@TarunChinmai/\
sharing-internet-connection-from-a-linux-machine-over-ethernet-a5cbbd775a4f

  args:
  interface - the name of the interface with the internet connection
  subnet - the subnet definition which the internet connection should be shared with

  TIPS - 
  to show the installed iptables rules, use 'sudo iptables -nvL' and
  'sudo iptables -t nat -nvL'

  to remove the iptables rules, use 'sudo iptables -F '

  "
}

if [ "$1" = "-h" ] 
then
  show_help
  exit 0
fi

if [ $# -ne 2 ]
then
 show_help 
 exit 1
else
  INTERFACE=$1
  SUBNET=$2
fi 

# enable forwarding
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null
# change srcip of all trafic from subnet to ip of $INTERFACE
sudo iptables -t nat -A POSTROUTING -o $INTERFACE -j MASQUERADE
# all packets from$SUBNET should be sent to $INTERFACE"
sudo iptables -I FORWARD -o $INTERFACE -s $SUBNET -j ACCEPT
# Accept all packets from $SUBNET even if they were not meant for this computer
sudo iptables -I INPUT -s $SUBNET -j ACCEPT

echo "The internet connection available on $INTERFACE is now shared to \
the $SUBNET subnet.
Don't forget to make sure that the clients on the subnet are using this \
computer's ip address as their default gateway (either using \
DHCP or manually)"


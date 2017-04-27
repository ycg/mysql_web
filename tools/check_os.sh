#!/bin/sh

#############################################
# Program : Check linux before install MySQL
# Author  : yxli 2017/04/27
# History :
#############################################

function printstr {
    if [ $2 -eq 1 ]
    then
      echo -e "[warning] "$1
    else
    echo -e "[info]    "$1
    fi
}

function check {
    echo ""
    printstr "Check start..." 0
    printstr "Linux Version : "`uname -r` 0
    printstr "IP : `ifconfig|grep "inet addr"|grep -v "127.0"|sed 's/inet addr://g'|awk '{print $1}'`" 0

    ## Hostname
    hostname=`hostname`
    if [ "localhost.localdomain" = "$hostname" ] || [ "" = "$hostname" ]
      then
        printstr "Hostname : Hostname is not set!" 1
    else
      printstr "Hostname : $hostname" 0
    fi

    ## Swap
    swap=`free -m|grep Swap|awk '{print $2}'`
    if [ 1024 -le $swap ]
      then
        printstr "Swap : Swap($swap"M") too large!" 1
    else
      printstr "Swap : $swap(M)" 0
    fi

    ## Firewall
    firewall=`chkconfig --list|grep iptables|sed 's/[0-9]://g'`
    if [ "echo $firewall|awk '{print $4}'" = "off" ] || [ "echo $firewall|awk '{print $5}'" = "on" ] || [ "echo $firewall|awk '{print $6}'" = "on" ] || [ "echo $firewall|awk '{print $7}'" = "on" ]
      then
      printstr "Firewall : Firewall is not closed!" 1
    else
      printstr "`chkconfig --list|grep iptables|sed 's/iptables/Iptables : /g'`" 0
    fi

    ## File system
    filesystem=0
    for i in `df -Thl|grep 'dev'|grep -v 'tmpfs'|awk '{print $2}'`
      do
        if [ "$i" != "ext4" ] && [ "$i" != "xfs" ]
          then
            filesystem=$((filesystem+1))
        fi
    done
    if [ 0 -lt $filesystem ]
      then
        printstr "File System : The file system is not ext4 or XFS!" 1
    else
      printstr "File System : `df -Thl|grep 'dev'|grep -v 'tmpfs'|awk '{print $1"|\t"$2"|\n"}'`" 0
    fi

    ## Selinux
    if [ `getenforce` != "Disabled" ]
      then
        printstr "Selinux is not closed!" 1
    else
      printstr "Selinux : `getenforce`" 0
    fi
    printstr "Check end!" 0
    echo ""
}

check

#!/usr/bin/python3

"""
Utility functions to help with network performance measurements
on AERPAW Backplane Network

@author: Harshvardhan P. Joshi, hpjoshi@ncsu.edu
"""
import os
import sys
import subprocess
import time
from datetime import datetime
import fcntl
import logging
import pingparser

logger = logging.getLogger("ap_utils")

def get_hostname():
    """
    Return the hostname
    """
    return os.uname()[1]



def run_cmd(command):
    """
    Run the given command as subprocess.check_output.
    Return the returncode and the output.
    The output is logged as debug.
    """
    try:
        logger.info("Running command: %s" % command)
        output = subprocess.check_output(command, shell=True,
                                         universal_newlines=True,
                                         stderr=subprocess.STDOUT)
        logger.debug(output)
        return 0, output
    except subprocess.CalledProcessError as err:
        logger.error("Failed: %s with returncode %d" %
                      (command, err.returncode))
        logger.debug(err.output)
        return err.returncode, err.output


def ping(hostname, count=5, interval=None, srcip=None):
    """
    Run ping to a host and return output and returncode
    """
    command = "ping -c%d %s" % (count, hostname)
    if interval is not None:
        command = command + " -i%.2f" % (interval)
    if srcip is not None:
        command = command + " -I%s" % (srcip)
    ret, output = run_cmd(command)
    return ret, output


def ping_parsed(hostname, count=5, timeout=None):
    """
    Run ping and return the output parsed as a dictionary object
    """
    ret, output = ping(hostname, count, timeout)
    parsedDict = pingparser.parse(output)
    return ret, parsedDict


def check_ping(hostname):
    """
    Check the reachability of a host
    """
    ret, output = ping(hostname, 1)
    return ret, output


def cycle_interface(intf):
    """
    Bring the interface down, and then up.
    """
    log = ""
    ret, output = run_cmd("ifdown %s" % intf)
    log = log + output
    ret, output = run_cmd("ifup %s" % intf)
    log = log + output

    return ret, log

def check_intf(intf, neighbor= None):
    """
    Check the status of the given network interface.
    If a neighbor is given, try contacting it.
    Return the log of the effort.
    """
    log = ""
    if neighbor is not None:
        ret, output = check_ping(neighbor)
        log = log + output
        if (ret == 0):
            return ret, log
    ret, output = run_cmd("ip address list %s" % intf)
    log = log + output
    if (ret != 0):
        return ret, log

    if "UP" not in output or "inet " not in output:
        logger.warning("Interface not up. Cycling interface %s" % intf)
        ret, output = cycle_interface(intf)
        log = log + output

    if neighbor is not None:
        ret, output = check_ping(neighbor)
        log = log + output
        if (ret != 0):
            logger.error("Cannot ping neighbor %s" % neighbor)

    return ret, log


def start_iperf_server(proto="tcp", iperf="iperf", timeout=20, port=None,
                       args=None):
    """
    Start iperf server with the given protocol, port and a timeout in seconds.
    If additional args are provided, they are also passed to iperf.
    """
    if (timeout == 0):
        # don't timeout
        command = ""
    else:
        command = "timeout %d " % timeout
    command = command + iperf + " -s"

    if iperf == "iperf":
    # dont do this for iperf3, it always runs both tcp and udp server
        if proto == "udp":
            command = command + " -u"
        elif proto != "tcp":
            logger.error("iperf using tcp, protocol %s not supported" % proto)

    if port is not None:
        command = command + (" -p%d" % port)
    if args is not None:
        command = command + " " + args

    ret, output = run_cmd(command)
    #ret, output = run_cmd_timeout(command, timeout)
    return ret, output


def start_iperf_client(server, iperf="iperf", proto="tcp", port=None,
                        pktsize=None, bandwidth=None, timeout=20, args=None):
    """
    Start iperf client with the given server, protocol, and port.
    If additional args are provided, they are also passed to iperf.
    """
    # Use timeout in case connection is not established
    command = "timeout %d %s -c %s" % (timeout, iperf, server)

    # get output in a format easy to process
    if iperf == "iperf":
        command = command + " -y C"
    else:
        command = command + " -J"
    if proto == "udp":
        command = command + " -u"
        if bandwidth is not None:
            command = command + (" -b%dM" % bandwidth)
    elif proto != "tcp":
        logger.error("Iperf using tcp, protocol %s not supported" % proto)

    if port is not None:
        command = command + (" -p%d" % port)

    if pktsize is not None:
        if proto == "udp":
            command = command + (" -l%d" % pktsize)
        else:
            command = command + (" -M%d" % pktsize)

    if args is not None:
        command = command + " " + args

    ret, output = run_cmd(command)
    return ret, output


def stop_iperf(iperf="iperf"):
    """
    Kill the iperf process(es)
    """
    logger.warning("Killing any %s processes" % iperf)
    command = "killall %s" % iperf
    ret, output = run_cmd(command)
    return ret, output

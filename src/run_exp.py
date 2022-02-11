#!/usr/bin/python3

"""
This script measures pair-wise latency between a given list
of network nodes. The nodes can be physical hosts or VMs/containers
running on such hosts. The nodes are uniquely identified by their
IP address.

@author: Harshvardhan P. Joshi, hpjoshi@gmail.com
"""
import argparse
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
import apexp
from ap_utils import *


def get_filenames(expid, exptype, logdir):
    myname = get_hostname()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    lfn = "log_%s_%s_%d_%s.txt" % (myname, exptype, expid, ts)
    logfile = os.path.join(logdir, lfn)
    cfn = "results_%s_%s_%d_%s.csv" % (myname, exptype, expid, ts)
    csvfile = os.path.join(logdir, cfn)
    return logfile, csvfile


def init_logging(logfile, verbose):
    logger = logging.getLogger('')
    ## config console logging with default level INFO
    ch = logging.StreamHandler(sys.stdout)
    if verbose.lower() == "debug":
        ch.setLevel(logging.DEBUG)
    elif verbose.lower() == "warning":
        ch.setLevel(logging.WARNING)
    elif verbose.lower() == "error":
        ch.setLevel(logging.ERROR)
    else:
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    ## config file logging
    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)-8s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.propagate = 0
    logger.setLevel(logging.DEBUG)

    return logger


def sync_from_client(remote_user, remote_ip, remote_dir, local_dir):
    cmd = "timeout %d rsync -az %s@%s:%s %s" % (30, remote_user,
                                                remote_ip, remote_dir, local_dir)
    ret, output = run_cmd(cmd)
    logger.debug(output)
    if ret == 0:
        logger.info("Success: sync from %s complete", remote_ip)
    else:
        logger.error("Fail: sync from %s could not be completed", remote_ip)


def run_remote_exp():
    """
    Run the experiment on a remote client through ssh
    """
    logger.info("Preparing remote experiments")
    # start a thread for each remote node

    # in each thread start the experiment locally
    cmd = "ssh %s@%s \"%s\"" % (remote_user, remote_ip, remote_cmd)

    # at the end sync remote logs and results to the master
    

def main():
    """
    Run experiments with
    Arguments:
        --runs, -r: the number of runs/repetitions for each experiment
        --period, -p: the time period between each run in seconds
        --logdir, -d: the directory in which to save the log and csv files
        --expid, -e: the experiment ID, to uniquely identify each
                    run of this script
        --conffile, -c: the configuration or parameters for the experiments,
                        which may be superseded by the CLI arguments above
        --verbose, -v: verbose/debug output
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument("-r", "--runs", type=int, default=50,
    #                     help="the number of runs/repetitions for each experiment")
    # parser.add_argument("-e", "--expid", type=int, default=1221,
    #                     help="the experiment ID, to uniquely identify each run of this script")
    # parser.add_argument("-v", "--verbose", default="WARNING",
    #                     help="verbosity level on console, default is WARNING")
    # parser.add_argument("-p", "--period", type=int, default=5,
    #                     help="the time period between each run in seconds")
    parser.add_argument("-d", "--logdir", default="/tmp/nsdi23/",
                        help="the directory used for log files, the file will be rotated every PERIOD minutes")
    parser.add_argument("-l", "--role", default="local",
                        help="role for this host: master|client|local")
    parser.add_argument("-m", "--masterip",
                        help="ip address of the master if the role is remote client")
    parser.add_argument("conffile",
                        help="the configuration for the experiments, may be superseded by CLI args")
    args = parser.parse_args()
    myname = get_hostname()

    # Read config file parameters
    print("Opening config file %s" % args.conffile)
    with open(args.conffile, "r", 1) as cf:
        config = json.load(cf)
    nruns = config["numRuns"]
    expid = config["expID"]
    logdir = config["logDir"]
    exptype = config["expType"]

    if role == "client" or  role == "local":
        logdir = os.path.join(logdir, myname)
    print("Creating log directory if it doesn't exist: %s" % logdir)
    ret, output = run_cmd("mkdir -p %s" % logdir)
    logfile, csvfile = get_filenames(expid, exptype, logdir)
    logger = init_logging(logfile, "info")

    print("Prepare experiment")
    logger.info("Prepare experiment")

    if role == "master":
        run_remote_exp(expid, logdir, config)
    else:
        exp = apexp.experiment(expid, logdir, config, csvfile, nruns=nruns)
        print("Start experiment")
        logger.info("Start experiment")
        exp.start()
        logger.info("End experiment")


if __name__ == "__main__":
    main()

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
import concurrent.futures
import logging
import logging.handlers
from datetime import datetime
import apexp
from ap_utils import *

logger = logging.getLogger('')

def get_logdir(config, role):
    myname = get_hostname()
    logdir = config["logDir"]
    if role == "worker":
        logdir = os.path.join(logdir, myname)
    return logdir


def get_filenames(expid, exptype, logdir):
    myname = get_hostname()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    lfn = "log_%s_%s_%d_%s.txt" % (myname, exptype, expid, ts)
    logfile = os.path.join(logdir, lfn)
    cfn = "results_%s_%s_%d_%s.csv" % (myname, exptype, expid, ts)
    csvfile = os.path.join(logdir, cfn)
    return logfile, csvfile


def init_logging(logfile, verbose):
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


def run_one_remote_exp(remote_ip, config):
    """
    Run the same experiment on a remote node
    """
    remote_user = config["remoteUser"]
    gitdir = config["gitDir"]
    remoteConfFile = config["remoteConfFile"]
    # in each thread start the experiment locally
    remote_cmd = "%s -l worker %s" % (os.path.join(gitdir, "src/run_exp.py"),
                                      os.path.join(gitdir, remoteConfFile))
    ssh_opts = "-o ConnectTimeout=10 -o StrictHostKeyChecking=no"
    cmd = "ssh %s %s@%s \"%s\"" % (ssh_opts, remote_user, remote_ip, remote_cmd)
    logger.info("Node %s: sending run experiment command: \"%s\"" % (remote_ip, cmd))
    ret, output = run_cmd(cmd)
    if ret != 0:
        logger.error("Experiment failed with:\n%s" % output)
    # at the end sync remote logs and results to the master
    local_logdir = get_logdir(config, "master")
    remote_dir = get_logdir(config, "worker")
    sync_from_client(remote_user, remote_ip, remote_dir, local_logdir)
    return 0


def run_remote_exp(config):
    """
    Run the experiment on a remote client through ssh
    """
    logger.info("Preparing remote experiments")
    nodes = config["nodes"]
    # start a thread for each remote node
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # create a dict of future to the node
        future_to_node = {executor.submit(run_one_remote_exp, node, config): node for node in nodes}
        for future in concurrent.futures.as_completed(future_to_node):
            node = future_to_node[future]
            try:
                ret = future.result()
            except Exception as e:
                logger.error("Node %s: generated exception: %s" % (node, e))
            else:
                logger.info("Node %s: experiment complete")
    

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
    parser.add_argument("-l", "--role", default="worker",
                        help="role for this host: master|worker")
    parser.add_argument("-m", "--masterip",
                        help="ip address of the master if the role is remote client")
    parser.add_argument("conffile",
                        help="the configuration for the experiments, may be superseded by CLI args")
    args = parser.parse_args()

    # Read config file parameters
    print("Opening config file %s" % args.conffile)
    with open(args.conffile, "r", 1) as cf:
        config = json.load(cf)
    nruns = config["numRuns"]
    expid = config["expID"]
    exptype = config["expType"]
    role = args.role
    logdir = get_logdir(config, role)

    print("Creating log directory if it doesn't exist: %s" % logdir)
    ret, output = run_cmd("mkdir -p %s" % logdir)
    logfile, csvfile = get_filenames(expid, exptype, logdir)
    logger = init_logging(logfile, "info")

    print("Prepare experiment")
    logger.info("Prepare experiment")

    if role == "master":
        print("Start remote experiment")
        run_remote_exp(config)
        print("End remote experiment")
    else:
        exp = apexp.experiment(expid, logdir, config, csvfile, nruns=nruns)
        print("Start experiment")
        logger.info("Start experiment")
        exp.start()
        logger.info("End experiment")


if __name__ == "__main__":
    main()

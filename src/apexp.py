"""
Contains the following class:
 - experiment: generic class for any experiment
 - explatency: runs latency experiments locally
"""

import os
import time
import apdelay
import csv
from ap_utils import *

EXPTYPES = ["latency", "runtime"]

class expruntime:
    """
    Run a given set of commands/scripts and time them.
    This will be used to measure the runtimes for experiment provisioning scripts.
    """
    def __init__(self, expid, csvfile, commands, nruns=1,
                 interval=1, config=None):
        self.expid = expid
        self.csvfile = csvfile
        self.commands = commands
        self.nruns = nruns
        self.interval = interval
        self.logger = logging.getLogger("runtime")
        self.config = config

    def start(self):
        """
        Start the provisioning experiment and measure runtime for each script
        """
        logger = self.logger
        hostname = get_hostname()
        for run in range(self.nruns):
            for cmd in self.commands:
                ## Careful what you allow to run as the given user
                logger.info("Starting command: %s" % (cmd))
                start_time = time.time()
                ret, output = run_cmd(cmd)
                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.info("Completed command in %d seconds" % (elapsed_time))


class explatency:
    """
    Run latency experiment locally.
    """
    def __init__(self, expid, csvfile, destips, nruns=30, srcips=None,
                 count=10, interval=0.3, runinterval=0, pktsizes=[64]):
        self.expid = expid
        self.csvfile = csvfile
        self.destips = []
        self.srcips = []
        self.nruns = nruns
        self.count = count
        self.interval = interval
        self.runinterval = runinterval
        self.pktsizes = pktsizes
        self.results = []
        self.reswriter = None
        self.logger = logging.getLogger("latency")
        if isinstance(destips, list):
            self.destips.extend(destips)
        else:
            self.destips.append(destips)
        if isinstance(srcips, list):
            self.srcips.extend(srcips)
        elif srcips is not None:
            self.srcips.append(srcips)

    def start_from(self, srcip=None):
        """
        Start the latency measurement from a given source IP address.
        """
        logger = self.logger
        hostname = get_hostname()
        for destip in self.destips:
            for pktsize in self.pktsizes:
                for run in range(self.nruns):
                    ad = apdelay.apdelay(destip, srcip=srcip, count=self.count,
                                         interval=self.interval)
                    ret, out = ad.ping()
                    if ret != 0 :
                        logger.error("Run %d: Ping to %s FAILED" % (run, destip))
                    else:
                        logger.info("Run %d: Ping to %s SUCCESS" % (run, destip))
                        # record to the experiment logs and results files
                        logger.debug(out)
                        # parse should return NaN for failed pings
                        parsed = ad.parse()
                        parsed.update({'expid': self.expid, 'runid': run, 'srcip': srcip,
                                       'interval': self.interval, 'pktsize': self.pktsizes,
                                       'hostname': hostname})
                        self.reswriter.writerow(parsed)
                        self.results.append(parsed)
                        # sleep if any
                        if self.runinterval > 0:
                            logger.debug("Run %d: Sleep for %d seconds before next run" %
                                         (run, self.runinterval))
                            time.sleep(self.runinterval)

    def start(self):
        """
        Start the latency measurement experiment.
        """
        attrs = vars(self)
        self.logger.debug("Explatency parameters:")
        self.logger.debug(', '.join("%s: %s" % item for item in attrs.items()))
        # write to csv as we do each run
        resfields = ['expid', 'hostname', 'srcip', 'dest', 'interval',
                     'pktsize', 'runid', 'sent', 'received', 'packet_loss',
                     'minping', 'avgping', 'maxping','jitter']
        with open(self.csvfile, 'w') as cf:
            self.reswriter = csv.DictWriter(cf, fieldnames=resfields)
            self.reswriter.writeheader()
            if len(self.srcips) == 0:
                self.start_from()
            else:
                for srcip in self.srcips:
                    self.start_from(srcip)
        return self.results


#########################

class experiment:
    """
    A generic AERPAW network measurement experiment class.
    Its main job is to provide a consistent logging and result
    collection framework.
    """
    def __init__(self, expid, logdir, config, csvfile, exptype="latency",
                 nruns=30, runinterval=5, verbose="INFO"):
        self.expid = expid
        self.exptype = exptype
        self.nruns = nruns
        self.logdir = logdir
        self.csvfile = csvfile
        self.verbose = verbose
        self.logger = logging.getLogger("apexp")
        self.runinterval = runinterval
        self.name = get_hostname()
        self.config = config
        # keep track of experiment progress
        self.runid = 0
        self.run_starttime = None

    def get_myips(self):
        """
        Return the list of IP addresses assigned to this host's interfaces
        """
        res, ips = run_cmd("hostname -I")
        if res != 0:
            raise Exception("Could not get host IP addresses:\n" + ips)
        myips = ips.strip().split(' ')
        self.logger.debug("My IPs: " + str(myips))
        return myips

    def get_srcips(self, myips, nodes):
        """
        Return the list of IP addresses on this host that are also part of
        the experiment.
        """
        if len(myips) == 1:
            srcips = myips
        else:
            srcips = set(myips).intersection(set(nodes))
            srcips = list(srcips)
        self.logger.debug("Source IPs: " + str(srcips))
        return srcips

    def get_destips(self, nodes, srcips=None, nodup=False):
        """
        Given a list of nodes, take out IP addresses belonging to us.
        If nodup is True, then only add "higher" IP addresses than the srcips
        """
        if srcips is None or len(srcips) == 0:
            self.logger.info("No srcips given, using all nodes as destination")
            return nodes

        destips = list(set(nodes) - set(srcips))
        if nodup == True and len(srcips) > 0:
            srcip = srcips[0] ## can only compare against one srcip
            filtered = [ip for ip in destips if ip > srcip]
            self.logger.debug("To eliminate pairwise duplication from srcip %s:" % srcip)
            self.logger.debug("  Original destips: " + str(destips))
            self.logger.debug("  Filtered destips: " + str(filtered))
            destips = filtered
        return destips


    def start(self):
        """
        Start the experiment.
        """
        logger = self.logger
        logger.info("Preparing %s experiment" %  self.exptype)
        # Print experiment parameters (attributes of self object)
        attrs = vars(self)
        logger.debug("Experiment parameters:")
        logger.debug(', '.join("%s: %s" % item for item in attrs.items()))
        if self.exptype == "latency":
            config = self.config
            count = config["pingRepeat"]
            interval = config["pingInterval"]
            pktsizes = config["pktSizes"]
            runinterval = config["runInterval"]
            nodes = config["nodes"]
            nodup = config["pairwiseNoDuplication"]
            myips = self.get_myips()
            srcips = self.get_srcips(myips, nodes)
            destips = self.get_destips(nodes, srcips, nodup=nodup)
            exp = explatency(self.expid, self.csvfile, destips, srcips=srcips,
                             nruns=self.nruns, count=count, interval=interval,
                             runinterval=runinterval, pktsizes=pktsizes)
            print("Starting %s experiment" % self.exptype)
            logger.info("Starting %s experiment" % self.exptype)
            try:
                res = exp.start()
            except Exception as e:
                logger.error("Failed to complete experiment. Error:\n" + e)

        elif self.exptype == "runtime":
            config = self.config
            commands = config["commands"]
            exp = expruntime(self.expid, self.csvfile, commands, nruns=1,
                             interval=0, config=config)
            print("Starting %s experiment" % self.exptype)
            logger.info("Starting %s experiment" % self.exptype)
            try:
                res = exp.start()
            except Exception as e:
                logger.error("Failed to complete experiment. Error:\n" + e)
        else:
            logger.error("Experiment type %s not supported (yet)" % self.exptype)

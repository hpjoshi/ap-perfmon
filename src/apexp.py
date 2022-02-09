"""
Contains the following class:
 - experiment: generic class for any experiment
 - explatency: runs latency experiments locally
"""

import os
import apdelay
import pandas as pd
from ap_utils import *

EXPTYPES = ["latency", "provisioning"]

class explatency:
    """
    Run latency experiment locally.
    """
    def __init__(self, expid, destips, runs=30, srcips=None,
                 count=10, interval=0.3, runinterval=0, pktsize=64):
        self.expid = expid
        self.destips = []
        self.srcips = []
        self.runs = runs
        self.count = count
        self.interval = interval
        self.runinterval = runinterval
        self.pktsize = pktsize
        self.results = []
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
        for destip in self.destips:
            for run in range(self.runs):
                ad = apdelay.apdelay(destip, srcip=srcip, count=self.count,
                                     interval=self.interval)
                ret, out = ad.ping()
                if ret != 0 :
                    logger.error("Runid %d: Ping to %s FAILED" % (run, destip))
                else:
                    logger.info("Runid %d: Ping to %s SUCCESS" % (run, destip))
                # record to the experiment logs and results files
                self.logger.debug(out)
                # parse should return NaN for failed pings
                parsed = ad.parse()
                parsed.update({'expid': self.expid, 'runid': run, 'src': srcip,
                               'interval': self.interval, 'pktsize': self.pktsize})
                self.results.append(parsed)
                # sleep if any
                if self.runinterval > 0:
                    time.sleep(self.runinterval)

    def start(self):
        """
        Start the latency measurement experiment.
        """
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
    def __init__(self, expid, logdir, config, exptype="latency",
                 nruns=30, runinterval=5, verbose="INFO", logger=None):
        self.expid = expid
        self.exptype = exptype
        self.nruns = nruns
        self.logdir = logdir
        self.csvfile = ""
        self.verbose = verbose
        self.runinterval = runinterval
        self.name = get_hostname()
        self.config = config
        # keep track of experiment progress
        self.runid = 0
        self.run_starttime = None
        self.setup_logging()
        self.setup_csv()

    def setup_logging(self):
        """
        Create the log files
        """
        filename = "log_%s_%s_%d.txt" % (self.name, self.exptype, self.expid)
        logfile = os.path.join(self.logdir, filename)

        ## config console logging with default level INFO
        ch = logging.StreamHandler()
        verbose = self.verbose
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
        logging.getLogger('').addHandler(ch)

        ## config file logging
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s.%(msecs)03d - [%(name)s] %(levelname)-8s: %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger('').addHandler(fh)

    def setup_csv(self):
        """
        Create the csv file for logging results
        """
        filename = "results_%s_%s_%d.csv" % (self.name, self.exptype, self.expid)
        self.csvfile = os.path.join(self.logdir, filename)
        
    def get_destips(self, nodes):
        """
        Given a list of nodes, take out IP addresses belonging to us
        """
        myips = run_cmd("hostname -I")[1].strip()
        destips = []
        for node in nodes:
            if node not in myips:
                destips.append(node)
        return destips

        
    def start(self):
        """
        Start the experiment.
        """
        logger = logging.getLogger('')
        logger.info("Preparing %s experiment" %  self.exptype)
        if self.exptype == "latency":
            config = self.config
            count = config["pingRepeat"]
            interval = config["pingInterval"]
            pktsizes = config["pktSizes"]
            pktsize = pktsizes[0]
            runinterval = config["runInterval"]
            nodes = config["nodes"]
            srcips = None ## Not supported yet
            destips = self.get_destips(nodes)
            exp = explatency(self.expid, destips, srcips=srcips,
                             runs=self.nruns, count=count, interval=interval,
                             runinterval=runinterval, pktsize=pktsize)
            logger.info("Starting %s experiment" % self.exptype)
            try:
                res = exp.start()
                df = pd.DataFrame(res)
                df.to_csv(self.csvfile)
            except Exception as e:
                logger.error("Failed to complete experiment. Error:\n" + e)

        else:
            logger.error("Experiment type %s not supported (yet)" % self.exptype)

        #logging.shutdown()


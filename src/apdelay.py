import pingparser
from ap_utils import *

class apping:
    """
    Measure latency between two nodes.
    """
    def __init__ (self, destip, srcip=None, count=3, interval=0.2):
        self.srcip = srcip
        self.destip = destip
        self.count = count
        self.interval = interval
        self.output = None
        self.dict = None

    def ping(self):
        """
        Run ping to a host and return output and returncode
        """
        command = "ping -c%d %s" % (self.count, self.destip)
        if self.interval is not None:
            command = command + " -i%.2f" % (self.interval)
        if self.srcip is not None:
            command = command + " -I%s" % (self.srcip)
        ret, output = run_cmd(command)
        self.output = str(output)
        return ret, self.output


    def parse(self):
        """
        Return the output of ping parsed as a dictionary object
        """
        if self.output is not None:
            self.dict = pingparser.parse(self.output)
        return self.dict


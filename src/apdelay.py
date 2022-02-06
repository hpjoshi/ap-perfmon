import pingparser
from ap_utils import *

class apdelay:
    """
    Measure latency between two nodes: localhost and destip.
    If multi-homed the source interface can be specified with srcip.
    The pings are repeated count times, and interval seconds are
    the time between each ping packet send.
    """
    def __init__ (self, destip, srcip=None, count=3, interval=0.2):
        self.srcip = srcip
        self.destip = destip
        self.count = count
        self.interval = interval
        self.pType = "ping"
        self.output = None
        self.pDict = None

    def ping(self):
        """
        Run ping to a host and return returncode and output
        """
        command = "ping -c%d %s" % (self.count, self.destip)
        if self.interval is not None:
            command = command + " -i%.2f" % (self.interval)
        if self.srcip is not None:
            command = command + " -I%s" % (self.srcip)
        ret, output = run_cmd(command)
        self.output = str(output)
        return ret, self.output


    def owping(self):
        """
        One-way ping using OWAMP tools from perfSonar.
        Currently not supported.
        """
        self.pType = "owping"
        return None


    def parse(self):
        """
        Return the output of ping parsed as a dictionary object
        """
        if self.output is not None:
            self.pDict = pingparser.parse(self.output)
        return self.pDict


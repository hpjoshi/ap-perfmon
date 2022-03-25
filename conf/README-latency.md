# Explanation of Latency Experiment Config Fields

Since the json file format does not allow comments (at least easily), we document the fields of the latency experiment config here.

The example below contains field names, example values, and explanation

``` json-with-comments
{
    "expID": 111, // Unique experiment ID, change this if any other field in this file changes
    "expType": "latency", // Type of the experiment. More types to be supported later
    "numRuns": 3, // Number of runs in each experiment. Should be 30 or more
    "logDir": "/home/aerpawops/nsdi23/results", // Directory where the logs and results are to be stored
    "verbose": "WARNING", // Level of verbosity on console. More relevant in `worker` mode
    "pingRepeat": 10, // No. of ping pkts to send in each run
    "pingInterval": 0.2, // Time interval in seconds between sending ping pkts, for ping arg `-i`
    "runInterval": 5, // Time interval in seconds to sleep before starting another run of the experiment
    "pktSizes": [64], // Pkt sizes to be used for ping
    "role": "worker", // Role of this node. Currently ignored and specified through cmdline
    "nodes": ["152.14.188.23",
              "152.14.188.24"], // The IP addresses of the nodes on which the experiments are to be run
    "pairwiseNoDuplication": false, // Do not duplicate for pair-wise experiments if this is set to `true`
    "remoteUser": "aerpawops", // Username for ssh
    "remoteConfFile": "conf/exp-111.json", // Config file for this experiment, used for remote experiments
    "gitRemote": "git@github.com:aerpawops/ap-perfmon.git", // URL for the git remote repository. If not specified, the default from src/prepare_worker.sh is used.
    "gitMasterDir": "/home/aerpawops/nsdi23/ap-perfmon", // Git directory on the `master`
    "gitDir": "/home/aerpawops/nsdi23/ap-perfmon" // Git directory for the `worker`
}
```

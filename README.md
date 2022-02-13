# ap-perfmon
AERPAW Network Performance Measurement

This repository contains the network performance measurement tools for AERPAW.

## Experiments List
- Pair-wise delay (latency) measurement
  - Substrate-to-substrate
  - Container-to-container
- Network provisioning and decommisioning time

## How-To
The ap-perfmon experiment framework can be used in a `master` or a `worker` mode. The `worker` mode runs the experiments on the local host and stores the logs and results of the experiment locally as well. The `master` mode allows starting experiments remotely on the specified `workers`, and then copy over the logs and results to the specified directory on the master.

### Master Mode
- Clone this repository to the `master` node, a node from where all worker nodes can be logged into with ssh.
- Create a json config file describing the experiment, based on examples in the conf directory of this repo.
- Commit and push the experiment config file to this repo in the conf directory.
- Start the experiment with `run_exp.py` specifying role as `master`. For example, from the repo root directory:
``` shell
src/run_exp.py conf/<experiment-config-json-file> -l master
```


### Worker Mode
- Clone this repository to the `worker` node.
- Create a json config file describing the experiment, based on examples in the conf directory of this repo.
- [Optional, but recommended] Commit and push the experiment config file to this repo in the conf directory.
- Start the experiment with `run_exp.py`. The default role is `worker` so the role does not have to be specified. For example, from the repo root directory:
``` shell
src/run_exp.py conf/<experiment-config-json-file>
```

## Open Questions
[x] Are we looking for completely handsfree experiment? Or manual experiment start on each pair?

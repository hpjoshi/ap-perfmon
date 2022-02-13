#!/bin/bash

####
# This script will prepare the worker node for experiments
# by creating the git repo (if needed) or pulling the latest
# code.

GIT_REMOTE="https://github.com/hpjoshi/ap-perfmon.git"

GIT_ROOT="$1"
GIT_BASE="$2"
GIT_FULLPATH="${GIT_ROOT}/${GIT_BASE}"

if [ -d "${GIT_FULLPATH}" ]
then
    echo "Git repo exists at ${GIT_FULLPATH}. Updating..."
    pushd "${GIT_FULLPATH}"
    git pull
    popd
else
    mkdir -p "${GIT_FULLPATH}"
    echo "Cloning git repo in ${GIT_FULLPATH}"
    pushd "${GIT_ROOT}"
    git clone "${GIT_REMOTE}" "${GIT_BASE}"
    popd
fi

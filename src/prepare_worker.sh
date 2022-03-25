#!/bin/bash

####
# This script will prepare the worker node for experiments
# by creating the git repo (if needed) or pulling the latest
# code.

if [ "$#" -lt 2 ]
then
    echo "Error: Usage: "
    echo "$0 <path to git repo parent dir> <gir repo dir name> [git ssh key] [git remote url]"
    exit 1
fi

GIT_ROOT="$1"
GIT_BASE="$2"
GIT_FULLPATH="${GIT_ROOT}/${GIT_BASE}"

if [ "$#" -ge 3 ]
then
    GIT_SSH_KEY="$3"
    GIT_SSH_CMD="ssh -i $GIT_SSH_KEY -o IdentitiesOnly=yes"
else
    GIT_SSH_CMD=""
fi

if [ "$#" -ge 4 ]
then
    GIT_REMOTE="$4"
else
    GIT_REMOTE="https://github.com/aerpawops/ap-perfmon.git"
fi

if [ -d "${GIT_FULLPATH}" ]
then
    echo "Git repo exists at ${GIT_FULLPATH}. Updating..."
    pushd "${GIT_FULLPATH}"
    GIT_SSH_COMMAND=${GIT_SSH_CMD} git pull
    popd
else
    mkdir -p "${GIT_FULLPATH}"
    echo "Cloning git repo in ${GIT_FULLPATH}"
    pushd "${GIT_ROOT}"
    GIT_SSH_COMMAND=${GIT_SSH_CMD} git clone "${GIT_REMOTE}" "${GIT_BASE}"
    popd
fi

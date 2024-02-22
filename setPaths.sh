#!/usr/bin/env bash

BHM_ENV=$1

export PYTHONPATH=$BHM_ENV:$PYTHONPATH
export PATH=$HOME/.local/bin:$PATH

echo $PYTHONPATH
echo $PATH

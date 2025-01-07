#!/bin/bash

cd /home/users/astephen/ai/ai-mini-projects/nc-archive-analysis
source ./setup-env.sh

python ./extract.py $@

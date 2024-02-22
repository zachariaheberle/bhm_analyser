#!/usr/bin/env bash

DIR=$1;

pip3 install pandas==1.5.1 scipy==1.9.1 seaborn==0.12.2 tk pylatex foliantcontrib.imagemagick --upgrade --target ${DIR}/
pip3 install scienceplots==2.0.1 --target ${DIR}/
pip3 install matplotlib==3.5.3 numpy==1.24.4 --upgrade --target ${DIR}/

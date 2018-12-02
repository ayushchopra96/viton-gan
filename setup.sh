#!/bin/bash

# Setup environment
pip install -r requirements.txt

# Clone repository for human parsing
cd ./human_parsing/LIP_JPPNet/checkpoint/
curl -L -o human_parsing_model.zip https://www.dropbox.com/sh/b54kk4asq9f3bgw/AADHgr29Hj-rystQCj1OFTmra\?dl\=1
unzip human_parsing_model.zip
cd ../../..

# Clone repository for pose estimation
cd pose_estimation/keras_Realtime_MultiPerson_Pose_Estimation/model/keras/
curl -L -o model.h5 https://www.dropbox.com/s/llpxd14is7gyj0z/model.h5
cd ../../../..

# Clone repository for try-on
cd try-on/VITON/model/
curl -L -o clothing_transfer_public_models.zip https://www.dropbox.com/sh/bxl1omic7o2yf4y/AABpnCFbh1Vr6W-xJqS8rGvqa\?dl\=1
unzip clothing_transfer_public_models.zip
cd ../../..
printf 'Completed.. exiting'

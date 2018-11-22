MODEL_NAME=satellite
MODEL_VERSION=v01
REQUEST_PATH=${PWD}/tensorflow-cnn/satellite_model

# predict using local file
IMG_PATH=/Users/ericbragas/galvanize/satellite-object-detection-case-study/data/imgs/no_ship/0__20150718_184300_090b__-122.40477488428849_37.8071040053892.png

# base 64 encode and create request msg in json format
python2 -c 'import base64, sys, json; img = base64.b64encode(open(sys.argv[1], "rb").read()); print json.dumps({"image_bytes": img})' $IMG_PATH &> ${REQUEST_PATH}/request.json
# "key": "1", 

# Local predict
MODEL_DIR=/Users/ericbragas/galvanize/satellite-object-detection-case-study/tensorflow-cnn/satellite_model/checkpoints/export/exporter/1542854719

gcloud ml-engine local predict \
    --model-dir=$MODEL_DIR \
    --json-instances=${REQUEST_PATH}/request.json \
    --verbosity=debug

# # ML Engine predict
# gcloud ml-engine predict \
#     --model=$MODEL_NAME \
#     --version=$MODEL_VERSION \
#     --json-instances=${REQUEST_PATH}/request.json

    # 1542846507
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import tensorflow as tf

# GPU 사용 가능 여부 확인
print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

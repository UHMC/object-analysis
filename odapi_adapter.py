# This is a modification of https://github.com/tensorflow/models/blob/master/object_detection/object_detection_tutorial.ipynb
# It is meant to be an adapter to provide object-detection information to image_strip.py and allow for its inclusion in the database.

# Imports
import os
import sys
import tarfile

import numpy as np
import six.moves.urllib as urllib
import tensorflow as tf
from PIL import Image

# Environment setup
# This is needed to fix import error by label_map_util in subdirectory.
sys.path.append("models")

# Object Detection Imports
from models.object_detection.utils import label_map_util
from models.object_detection.utils import visualization_utils as vis_util

# Variables (model to download)
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
MODEL_FILE = MODEL_NAME + '.tar.gz'
DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

# List of the strings that is used to add a correct label for each box.
PATH_TO_LABELS = os.path.join('models', 'object_detection', 'data', 'mscoco_label_map.pbtxt')
NUM_CLASSES = 90

# Download the model
opener = urllib.request.URLopener()
opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
tar_file = tarfile.open(MODEL_FILE)
for file in tar_file.getmembers():
    file_name = os.path.basename(file.name)
    if 'frozen_inference_graph.pb' in file_name:
        tar_file.extract(file, os.getcwd())

# Load frozen TensorFlow model
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

# Load label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)


# Helper function
def load_image_into_numpy_array(image):
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)


def get_objects(image_path):
    # Detection
    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            image = Image.open(image_path)
            # the array based representation of the image will be used later in order to prepare the
            # result image with boxes and labels on it.
            image_np = load_image_into_numpy_array(image)
            # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
            image_np_expanded = np.expand_dims(image_np, axis=0)
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            scores = detection_graph.get_tensor_by_name('detection_scores:0')
            classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')
            # Actual detection.
            (boxes, scores, classes, num_detections) = sess.run(
                [boxes, scores, classes, num_detections],
                feed_dict={image_tensor: image_np_expanded})
            # image_np: uint8 numpy array with shape (img_height, img_width, 3)
            # boxes: a numpy array of shape [N, 4]
            # classes: a numpy array of shape [N]
            # scores: a numpy array of shape [N] or None.
            # category_index: a dict containing category dictionaries (each holding
            #   category index `id` and category name `name`) keyed by category indices.
            return (
                image_np,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index
            )

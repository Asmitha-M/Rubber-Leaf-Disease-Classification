import os
import numpy as np
import tensorflow as tf
from PIL import Image

# Recreate the model structure exactly as in train_model.py
DATASET_DIR = r"d:\Rubber android app new\Dataset"
IMAGE_SIZE = (224, 224)
NUM_CLASSES = 8

inputs = tf.keras.layers.Input(shape=(224, 224, 3))
# Data augmentation is identity during inference
data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.2),
    tf.keras.layers.RandomZoom(0.1),
])
augmented = data_augmentation(inputs)

preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input
preprocessed = preprocess_input(augmented)

base_model = tf.keras.applications.MobileNetV2(
    input_tensor=preprocessed,
    include_top=False,
    weights="imagenet"
)

x = base_model.output
conv_classifier = tf.keras.layers.Conv2D(NUM_CLASSES, (1, 1), padding="same", name="conv_classifier")(x)
pooled = tf.keras.layers.GlobalAveragePooling2D()(conv_classifier)
outputs = tf.keras.layers.Activation("softmax", name="dense_classifier")(pooled)

model = tf.keras.models.Model(inputs=inputs, outputs=outputs)

# Load the saved weights
temp_weights_path = r"d:\Rubber android app new\app\src\main\assets\temp_weights.weights.h5"
# Wait, did we delete it? If deleted, let's look for model.tflite or check if we can save weights to another path during training.
# Since we deleted it, let's load the weights from assets if they exist, or check if we can inspect the graph.
# Wait! Let's modify train_model.py to NOT delete temp_weights.weights.h5 so we can inspect it!
print("Weights path exists:", os.path.exists(temp_weights_path))

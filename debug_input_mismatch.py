import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory
from PIL import Image

# Recreate the model structure
DATASET_DIR = r"d:\Rubber android app new\Dataset"
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
NUM_CLASSES = 8

inputs = tf.keras.layers.Input(shape=(224, 224, 3))
preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input
preprocessed = preprocess_input(inputs)

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

# Load the weights we saved
# (Since we deleted it in train_model.py, we can just run a single epoch training or load it from the asset tflite using the interpreter)
# Wait, let's load model.tflite via the interpreter and run it on val_ds!
tflite_path = r"d:\Rubber android app new\app\src\main\assets\model.tflite"
interpreter = tf.lite.Interpreter(model_path=tflite_path)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("=== INSPECTING DATASET IMAGES ===")
# Get the first image path from dataset to compare directly
classes = ['Abnormal', 'Anthracnose', 'Black_Spot', 'Dry_Leaf', 'Healthy', 'Leaf_Blight', 'Leaf_Spot', 'Powdery_Mildew']
target_class = 'Abnormal'
img_file = os.listdir(os.path.join(DATASET_DIR, target_class))[0]
img_path = os.path.join(DATASET_DIR, target_class, img_file)

# 1. Load manually via PIL
img_pil = Image.open(img_path).resize((224, 224))
img_pil_arr = np.array(img_pil, dtype=np.float32)
print(f"PIL Image Info:")
print(f"  Shape: {img_pil_arr.shape}")
print(f"  Min:   {img_pil_arr.min()}")
print(f"  Max:   {img_pil_arr.max()}")
print(f"  Mean:  {img_pil_arr.mean()}")

# 2. Load via tf.keras.utils.load_img & img_to_array (which is what Keras uses internally)
img_keras = tf.keras.utils.load_img(img_path, target_size=(224, 224))
img_keras_arr = tf.keras.utils.img_to_array(img_keras)
print(f"Keras Image Info:")
print(f"  Shape: {img_keras_arr.shape}")
print(f"  Min:   {img_keras_arr.min()}")
print(f"  Max:   {img_keras_arr.max()}")
print(f"  Mean:  {img_keras_arr.mean()}")

# 3. Load via tf.io.read_file + decode_jpeg
img_raw = tf.io.read_file(img_path)
img_tf = tf.image.decode_jpeg(img_raw, channels=3)
img_tf_resized = tf.image.resize(img_tf, [224, 224])
img_tf_arr = img_tf_resized.numpy()
print(f"TF Decode Image Info:")
print(f"  Shape: {img_tf_arr.shape}")
print(f"  Min:   {img_tf_arr.min()}")
print(f"  Max:   {img_tf_arr.max()}")
print(f"  Mean:  {img_tf_arr.mean()}")

# Let's compare PIL vs TF arrays difference
diff = np.abs(img_pil_arr - img_tf_arr)
print(f"Max difference between PIL and TF Decode: {diff.max()}")

# Run TFLite inference on PIL preprocessed image
img_pil_preprocessed = (img_pil_arr / 127.5) - 1.0
img_pil_preprocessed = np.expand_dims(img_pil_preprocessed, axis=0)
interpreter.set_tensor(input_details[0]['index'], img_pil_preprocessed)
interpreter.invoke()
probs_pil = interpreter.get_tensor(output_details[1]['index'])[0]

# Run TFLite inference on TF preprocessed image
img_tf_preprocessed = (img_tf_arr / 127.5) - 1.0
img_tf_preprocessed = np.expand_dims(img_tf_preprocessed, axis=0)
interpreter.set_tensor(input_details[0]['index'], img_tf_preprocessed)
interpreter.invoke()
probs_tf = interpreter.get_tensor(output_details[1]['index'])[0]

print(f"\nPredictions for PIL:")
print(f"  {', '.join([f'{c}: {p*100:.1f}%' for c, p in zip(classes, probs_pil)])}")
print(f"Predictions for TF:")
print(f"  {', '.join([f'{c}: {p*100:.1f}%' for c, p in zip(classes, probs_tf)])}")

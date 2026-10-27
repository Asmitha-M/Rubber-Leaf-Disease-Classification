import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image_dataset_from_directory
from tensorflow.keras import layers, models, Model

# Set random seed for reproducibility
tf.random.set_seed(42)
np.random.seed(42)

# Configurations
DATASET_DIR = r"d:\Rubber android app new\Dataset"
ASSETS_DIR = r"d:\Rubber android app new\app\src\main\assets"
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS_FREEZE = 12
EPOCHS_FINE = 8
NUM_CLASSES = 9

# Create assets folder if not exists
os.makedirs(ASSETS_DIR, exist_ok=True)

print("--- Loading Dataset ---")
train_ds = image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

val_ds = image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int"
)

class_names = train_ds.class_names
print(f"Class Names: {class_names}")

# Configure dataset for performance
AUTOTUNE = tf.data.AUTOTUNE

# Data augmentation block applied directly to training dataset
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.2),
    layers.RandomZoom(0.15),
    layers.RandomTranslation(0.1, 0.1),
    layers.RandomContrast(0.15),
    layers.RandomBrightness(0.15)
])

train_ds = train_ds.cache()
train_ds = train_ds.map(lambda x, y: (data_augmentation(x, training=True), y), num_parallel_calls=AUTOTUNE)
train_ds = train_ds.shuffle(1000).prefetch(buffer_size=AUTOTUNE)

val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

print("--- Building MobileNetV2 Model (Flat Graph) ---")
# Input tensor
inputs = layers.Input(shape=(224, 224, 3))

# Preprocessing
preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input
preprocessed = preprocess_input(inputs)

# Base pre-trained model instantiated standalone
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False  # Freeze base model

# Pass preprocessed tensor through the base model
features_output = base_model(preprocessed)

# Classification head using 1x1 Conv to avoid FULLY_CONNECTED version 12 in TFLite
conv_classifier = layers.Conv2D(NUM_CLASSES, (1, 1), padding="same", name="conv_classifier")(features_output)
pooled = layers.GlobalAveragePooling2D()(conv_classifier)
dropout = layers.Dropout(0.3, name="classifier_dropout")(pooled)
outputs = layers.Activation("softmax", name="dense_classifier")(dropout)

# Main model for training
model = Model(inputs=inputs, outputs=outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

print("--- Defining Optimization Callbacks ---")
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True
)

reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.2,
    patience=2,
    min_lr=1e-6
)

print("--- Training Base Model ---")
history = model.fit(
    train_ds,
    epochs=EPOCHS_FREEZE,
    validation_data=val_ds,
    callbacks=[early_stopping, reduce_lr]
)

print("--- Fine-tuning Top Layers ---")
# Unfreeze base model and freeze all but the last blocks
base_model.trainable = True
# Freeze layers up to layer 100
for layer in base_model.layers[:100]:
    layer.trainable = False
# Explicitly keep all Batch Normalization layers frozen to maintain stable ImageNet statistics
for layer in base_model.layers:
    if "BatchNormalization" in layer.__class__.__name__:
        layer.trainable = False

# Recompile with lower learning rate
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.00001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

history_fine = model.fit(
    train_ds,
    epochs=EPOCHS_FINE,
    validation_data=val_ds,
    callbacks=[early_stopping, reduce_lr]
)

print("--- Extracting Final Conv Layer Weights for Grad-CAM ---")
conv_layer = model.get_layer("conv_classifier")
weights, biases = conv_layer.get_weights()
# weights shape: (1, 1, 1280, NUM_CLASSES)
weights_reshaped = weights.reshape(1280, NUM_CLASSES)

weights_path = os.path.join(ASSETS_DIR, "dense_weights.bin")
weights_reshaped.astype(np.float32).tofile(weights_path)
print(f"Dense weights saved to: {weights_path}")

# Save trained model weights to temporary file
temp_weights_path = os.path.join(ASSETS_DIR, "temp_weights.weights.h5")
model.save_weights(temp_weights_path)

print("--- Building Multi-Output Inference Model ---")
# Output both classification probabilities and base model output (feature map out_relu)
inference_model = Model(
    inputs=inputs,
    outputs=[model.output, features_output]
)
# Load the trained weights into the inference model structure
inference_model.load_weights(temp_weights_path)

# Cleanup temporary weights file
if os.path.exists(temp_weights_path):
    os.remove(temp_weights_path)

print("--- Converting Model to TFLite ---")
converter = tf.lite.TFLiteConverter.from_keras_model(inference_model)
tflite_model = converter.convert()

tflite_model_path = os.path.join(ASSETS_DIR, "model.tflite")
with open(tflite_model_path, "wb") as f:
    f.write(tflite_model)
print(f"Multi-output TFLite model saved to: {tflite_model_path}")

print("--- Verification Check ---")
interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print(f"TFLite Input details: {input_details[0]['shape']}")
print(f"TFLite Output 1 (Classification) details: {output_details[0]['shape']}")
print(f"TFLite Output 2 (Feature Map) details: {output_details[1]['shape']}")

print("\nAll model artifacts generated successfully!")

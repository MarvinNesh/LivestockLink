import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Sequential
import os
import numpy as np


DATA_DIR = 'data/poultry_diseases'  
IMG_SIZE = 224
BATCH_SIZE = 16  
EPOCHS = 10  
CLASSES = ['Healthy', 'Newcastle', 'Coccidiosis', 'Salmonella']  

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True,
    shear_range=0.2,
    validation_split=0.2  
)
train_gen = train_datagen.flow_from_directory(
    DATA_DIR, target_size=(IMG_SIZE, IMG_SIZE), batch_size=BATCH_SIZE,
    class_mode='categorical', classes=CLASSES, subset='training' 
)
val_gen = train_datagen.flow_from_directory(
    DATA_DIR, target_size=(IMG_SIZE, IMG_SIZE), batch_size=BATCH_SIZE,
    class_mode='categorical', classes=CLASSES, subset='validation'
)


base = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights='imagenet')
base.trainable = False  


model = Sequential([
    base,
    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dense(len(CLASSES), activation='softmax') 
])
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("Training...")
history = model.fit(train_gen, epochs=EPOCHS, validation_data=val_gen)


val_loss, val_acc = model.evaluate(val_gen)
print(f"Validation Accuracy: {val_acc:.2%}")


converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open('poultry_disease_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("✅ poultry_disease_model.tflite saved! Update MODEL_PATH in routes.py.")
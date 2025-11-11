from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import shutil
from . import scanner_bp
import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter  


UPLOAD_FOLDER = 'static/uploads/scanner'  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


MODEL_PATH = 'poultry_disease_model.tflite'  
LABELS_PATH = 'imagenet_labels.txt' 



def analyze_image(image_path):
    """Analyzes uploaded image for poultry disease symptoms using fine-tuned ML."""
    # Load and preprocess image
    image = cv2.imread(image_path)
    if image is None:
        return {'diagnosis': 'Error: Invalid image', 'confidence': '0%', 'recommendation': 'Try uploading again.'}
    
    # Convert BGR to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize to model input size (224x224)
    input_size = 224
    image_resized = cv2.resize(image, (input_size, input_size))
    image_normalized = image_resized.astype(np.float32) / 255.0
    input_tensor = np.expand_dims(image_normalized, axis=0)
    
    try:
        # Load TFLite model and run inference
        interpreter = Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        interpreter.set_tensor(input_details[0]['index'], input_tensor)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        # Poultry-specific labels (alphabetical from dataset)
        labels = ['Coccidiosis', 'Healthy', 'Newcastle', 'Salmonella']
        
        
        prediction = np.argmax(output_data[0])
        
        confidence = float(np.max(output_data[0]))
        
        # Safe indexing
        if 0 <= prediction < len(labels):
            diagnosis = labels[prediction]
        else:
            diagnosis = f'Unknown (index {prediction} out of 0-{len(labels)-1})'
        
        
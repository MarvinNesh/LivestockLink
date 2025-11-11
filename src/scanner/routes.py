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
        
        # SA-specific recommendations
        recs = {
            'Healthy': 'Animal looks healthy—continue routine monitoring and biosecurity.',
            'Newcastle': 'Urgent: Newcastle disease detected. Isolate affected birds immediately, vaccinate flock if not done. Contact DAFF hotline (0800 00 9999) for free advice/outbreak report. Losses can reach 90% without action.',
            'Coccidiosis': 'Coccidiosis suspected (bloody droppings?). Treat with anticoccidials (e.g., Amprolium from co-op). Clean coop, avoid overcrowding. Common in wet seasons—consult local vet.',
            'Salmonella': 'Salmonella alert (diarrhea/green droppings?). Quarantine, use antibiotics via vet prescription. Report to DAFF for flock testing. Prevent via clean water/feed.'
        }
        recommendation = recs.get(diagnosis, 'Consult a vet for further tests.')
        
        return {
            'diagnosis': diagnosis,
            'confidence': f"{confidence:.2%}",
            'recommendation': recommendation
        }
    
    except Exception as e:
        print(f"Inference error: {str(e)}")
        return {'diagnosis': f'Analysis error: {str(e)}', 'confidence': '0%', 'recommendation': 'Model issue—check logs.'}

@scanner_bp.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner():
    """Handles symptom scanner page and image upload/analysis."""
    if request.method == 'POST':
        # Check for 'image' to match template; fallback to 'file'
        file_key = 'image' if 'image' in request.files else 'file'
        if file_key not in request.files:
            return jsonify({'error': 'No file uploaded.'}), 400
        
        file = request.files[file_key]
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            result = analyze_image(filepath)
            print(result)
            
            # Move to processed for preview (instead of remove)
            processed_folder = os.path.join(UPLOAD_FOLDER, 'processed')
            os.makedirs(processed_folder, exist_ok=True)
            shutil.move(filepath, os.path.join(processed_folder, filename))
            
            return jsonify({
                'filename': f'processed/{filename}',  # Updated for preview path
                'diagnosis': result['diagnosis'],
                'confidence': result['confidence'],
                'recommendation': result['recommendation']
            })
        
        return jsonify({'error': 'Invalid file type.'}), 400
    
    return render_template('scanner.html')
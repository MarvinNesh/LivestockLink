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


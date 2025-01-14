import os
from flask import Flask, request, jsonify, render_template
from tensorflow.keras.models import load_model
import numpy as np
import cv2
from flask_cors import CORS
import logging

app = Flask(__name__, static_folder='styles', template_folder='.')

CORS(app, origins=["https://pawdentity.netlify.app/", "http://localhost:5000/"])

MODEL_PATH = 'models/cat_dog_classifier.h5'
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = load_model(MODEL_PATH)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        img = cv2.resize(img, (128, 128))  
        img = img / 255.0  
        img = np.expand_dims(img, axis=0)  
    return img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['image']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        img = preprocess_image(file_path)
        prediction = model.predict(img)[0][0]
        category = 'Dog' if prediction > 0.5 else 'Cat'

        os.remove(file_path)
        return jsonify({'category': category})
    except Exception as e:
        app.logger.error(f"Error in classification: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

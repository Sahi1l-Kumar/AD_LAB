import os
from flask import Flask, request, jsonify, render_template
from tensorflow.keras.models import load_model
import numpy as np
import cv2

app = Flask(__name__, static_folder='styles', template_folder='../Lab2')

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

if __name__ == '__main__':
    app.run(debug=True)

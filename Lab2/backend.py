import os
from flask import Flask, request, jsonify, render_template
from tensorflow.keras.models import load_model
import numpy as np
import cv2

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure paths
MODEL_PATH = 'models/cat_dog_classifier.h5'
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the trained model
model = load_model(MODEL_PATH)

# Explicitly compile the model to avoid warnings about missing compiled metrics
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Preprocess the image
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        img = cv2.resize(img, (128, 128))  # Resize to match model input
        img = img / 255.0  # Normalize
        img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Classify route
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

    os.remove(file_path)  # Clean up uploaded file
    return jsonify({'category': category})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

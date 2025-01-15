import os
from flask import Flask, request, jsonify, render_template
import numpy as np
import cv2
from flask_cors import CORS
import joblib
from tensorflow.keras.models import load_model

app = Flask(__name__, static_folder='styles', template_folder='.')
CORS(app, origins=["http://localhost:5000/"])

UPLOAD_FOLDER = 'uploads'
MODEL_FOLDER = 'models'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

cnn_model = load_model(os.path.join(MODEL_FOLDER, 'cnn_model.h5'))
svm_model = joblib.load(os.path.join(MODEL_FOLDER, 'svm_model.pkl'))
rf_model = joblib.load(os.path.join(MODEL_FOLDER, 'random_forest_model.pkl'))
logreg_model = joblib.load(os.path.join(MODEL_FOLDER, 'logistic_regression_model.pkl'))
kmeans_model = joblib.load(os.path.join(MODEL_FOLDER, 'kmeans_model.pkl'))

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is not None:
        img = cv2.resize(img, (128, 128)) 
        img = img / 255.0 
        img = np.expand_dims(img, axis=0) 
    return img

def map_output(model_type, raw_output):
    """Map the raw output of models to consistent categories."""
    if model_type == 'svm':
        return 'Cat' if raw_output == 0 else 'Dog'
    elif model_type == 'random_forest':
        return 'Dog' if raw_output == 0 else 'Cat'
    elif model_type == 'logistic_regression':
        return 'Cat' if raw_output == 0 else 'Dog' 
    elif model_type == 'kmeans':
        return f'Cluster {raw_output}'
    return 'Unknown'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_image():
    try:
    
        if 'image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['image']
        model_type = request.form.get('model', 'cnn') 
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

    
        img = preprocess_image(file_path)

    
        category = 'Unknown'
        if model_type == 'cnn':
            prediction = cnn_model.predict(img)[0][0]
            category = 'Dog' if prediction > 0.5 else 'Cat'
        elif model_type in ['svm', 'random_forest', 'logistic_regression', 'kmeans']:
            img_flattened = img.flatten().reshape(1, -1) 
            raw_output = None
            if model_type == 'svm':
                raw_output = int(svm_model.predict(img_flattened)[0])
            elif model_type == 'random_forest':
                raw_output = int(rf_model.predict(img_flattened)[0])
            elif model_type == 'logistic_regression':
                raw_output = int(logreg_model.predict(img_flattened)[0])
            elif model_type == 'kmeans':
                raw_output = int(kmeans_model.predict(img_flattened)[0])

            category = map_output(model_type, raw_output)
        else:
            return jsonify({'error': 'Invalid model selection'}), 400

        os.remove(file_path)
        return jsonify({'category': category})
    except Exception as e:
        app.logger.error(f"Error in classification: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

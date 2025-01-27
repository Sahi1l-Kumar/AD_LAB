from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import pandas as pd
from flask_cors import CORS


app = Flask(__name__, static_folder='styles', template_folder='.')
CORS(app, origins=["http://localhost:5000/"])

# Load the trained model and scaler
model = joblib.load('models/linear_model.pkl')
scaler = joblib.load('models/scaler.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input data from request
        data = request.json
        stock_symbol = data['Symbol']
        prediction_days = int(data['Days'])

        # Placeholder values for demo purposes
        # You might need to actually fetch data based on the stock symbol
        open_price, high_price, low_price, volume = 1000, 1050, 980, 2000000

        # Prepare input for model
        input_features = np.array([[open_price, high_price, low_price, volume]])
        input_scaled = scaler.transform(input_features)

        # Predict stock price
        predicted_price = model.predict(input_scaled)[0]

        return jsonify({
            'predicted_price': round(predicted_price, 2),
            'symbol': stock_symbol,
            'days': prediction_days
        })
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
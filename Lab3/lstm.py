import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
import json

np.random.seed(42)
tf.random.set_seed(42)

df = pd.read_csv("datasets/airtel_df.csv") 

df = df[['Date', 'Close']].dropna()

df['Date'] = pd.to_datetime(df['Date'])

df = df.sort_values(by='Date')

scaler = MinMaxScaler(feature_range=(0, 1))
df['Close_Scaled'] = scaler.fit_transform(df[['Close']])

X = np.arange(len(df)).reshape(-1, 1) 
y = df['Close_Scaled'].values

if np.isnan(y).any():
    raise ValueError("Processed target variable contains NaN values. Check dataset.")

linear_model = LinearRegression()
linear_model.fit(X, y)
linear_pred = linear_model.predict(X)
linear_pred = scaler.inverse_transform(linear_pred.reshape(-1, 1))

def create_lstm_dataset(data, lookback=5):
    X_lstm, y_lstm = [], []
    for i in range(len(data) - lookback):
        X_lstm.append(data[i:i + lookback])
        y_lstm.append(data[i + lookback])
    return np.array(X_lstm), np.array(y_lstm)

lookback = 5
X_lstm, y_lstm = create_lstm_dataset(df['Close_Scaled'].values, lookback)

X_lstm = X_lstm.reshape((X_lstm.shape[0], X_lstm.shape[1], 1))

lstm_model = tf.keras.Sequential([
    tf.keras.layers.LSTM(50, activation='relu', input_shape=(lookback, 1)),
    tf.keras.layers.Dense(1)
])

lstm_model.compile(optimizer='adam', loss='mse')
lstm_model.fit(X_lstm, y_lstm, epochs=10, batch_size=1, verbose=0)

lstm_predictions = lstm_model.predict(X_lstm)
lstm_predictions = scaler.inverse_transform(lstm_predictions)

output_data = {
    "LinearRegression": [{"date": str(df['Date'].iloc[i].date()), "value": float(linear_pred[i])} for i in range(len(linear_pred))],
    "LSTM": [{"date": str(df['Date'].iloc[i+lookback].date()), "value": float(lstm_predictions[i])} for i in range(len(lstm_predictions))]
}

with open("predictions.json", "w") as f:
    json.dump(output_data, f, indent=4)

print("Predictions saved to predictions.json")

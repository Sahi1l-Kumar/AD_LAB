import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from math import sqrt
import joblib

def preprocess_data(file_path):
    data = pd.read_csv(file_path)
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index('Date', inplace=True)

    data = data.dropna()

    X = data[['Open', 'High', 'Low', 'Volume']]
    y = data['Close']

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    return X_train, X_test, y_train, y_test, scaler

def train_linear_regression(X_train, y_train):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    from math import sqrt
    rmse = sqrt(mean_squared_error(y_test, y_pred))
    return rmse


def predict_stock_price(model, input_data):
    return model.predict(input_data)

if __name__ == '__main__':
    file_path = 'datasets/airtel_df.csv'
    X_train, X_test, y_train, y_test, scaler = preprocess_data(file_path)

    model = train_linear_regression(X_train, y_train)

    rmse = evaluate_model(model, X_test, y_test)
    print(f'Linear Regression RMSE: {rmse}')

    joblib.dump(model, 'models/linear_model.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')

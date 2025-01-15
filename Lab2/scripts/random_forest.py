from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np
import cv2
import os

dataset_path = 'datasets'

images, labels = [], []
for label, category in enumerate(os.listdir(dataset_path)):
    category_path = os.path.join(dataset_path, category)
    for img_file in os.listdir(category_path):
        img = cv2.imread(os.path.join(category_path, img_file))
        if img is not None:
            img = cv2.resize(img, (128, 128))
            images.append(img.flatten())
            labels.append(label)

X = np.array(images)
y = np.array(labels)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_train, y_train)

os.makedirs('models', exist_ok=True)
joblib.dump(rf_model, 'models/random_forest_model.pkl')

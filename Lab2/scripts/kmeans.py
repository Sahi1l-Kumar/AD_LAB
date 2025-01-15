from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np
import cv2
import os

dataset_path = 'datasets'

images = []
for category in os.listdir(dataset_path):
    category_path = os.path.join(dataset_path, category)
    for img_file in os.listdir(category_path):
        img = cv2.imread(os.path.join(category_path, img_file))
        if img is not None:
            img = cv2.resize(img, (128, 128))
            images.append(img.flatten())

X = np.array(images)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans_model = KMeans(n_clusters=2, random_state=42)
kmeans_model.fit(X_scaled)

os.makedirs('models', exist_ok=True)
joblib.dump(kmeans_model, 'models/kmeans_model.pkl')

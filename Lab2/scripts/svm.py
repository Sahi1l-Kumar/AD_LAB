from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import numpy as np
import tqdm 
import cv2
import os

try:
    import cupy as cp 
    gpu_enabled = True
except ImportError:
    cp = np 
    gpu_enabled = False

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

X = cp.array(images)
y = cp.array(labels)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(cp.asnumpy(X)) 

X_train, X_test, y_train, y_test = train_test_split(X_scaled, cp.asnumpy(y), test_size=0.2, random_state=42)

svm_model = SVC(kernel='linear', probability=True)

batch_size = 100
num_batches = len(X_train) // batch_size + 1

print("Training SVM...")
for i in tqdm.tqdm(range(num_batches), desc="Training Progress"):
    start = i * batch_size
    end = min(start + batch_size, len(X_train))
    batch_X = X_train[start:end]
    batch_y = y_train[start:end]
    if len(batch_X) > 0:
        svm_model.fit(batch_X, batch_y) 

os.makedirs('models', exist_ok=True)
joblib.dump(svm_model, 'models/svm_model.pkl')

print("Training complete. Model saved at 'models/svm_model.pkl'.")

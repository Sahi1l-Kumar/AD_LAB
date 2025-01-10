import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt

# Dataset path (update this to your dataset location)
dataset_path = 'datasets'

# Data generator for training and validation
datagen = ImageDataGenerator(
    rescale=1.0 / 255.0,  # Normalize pixel values to [0, 1]
    validation_split=0.2  # Reserve 20% of data for validation
)

# Training data generator
train_generator = datagen.flow_from_directory(
    dataset_path,
    target_size=(128, 128),  # Resize images to 128x128
    batch_size=32,
    class_mode='binary',  # Binary classification: cats and dogs
    subset='training'  # Use 80% of data for training
)

# Validation data generator
validation_generator = datagen.flow_from_directory(
    dataset_path,
    target_size=(128, 128),
    batch_size=32,
    class_mode='binary',
    subset='validation'  # Use 20% of data for validation
)

# Build the CNN model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    MaxPooling2D(pool_size=(2, 2)),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')  # Binary classification
])

# Compile the model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
history = model.fit(
    train_generator,
    validation_data=validation_generator,
    epochs=20
)

# Save the trained model
model_save_path = './models/cat_dog_classifier.h5'
os.makedirs(os.path.dirname(model_save_path), exist_ok=True)  # Ensure save directory exists
model.save(model_save_path)
print(f"Model saved to {model_save_path}")

# Plot training and validation accuracy
plt.figure(figsize=(8, 6))
plt.plot(history.history['accuracy'], label='Train Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.show()
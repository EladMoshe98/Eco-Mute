from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib

#1. Generate synthetic data
#
n_samples = 1000
distance = np.random.uniform(1, 20, n_samples)
battery_levels = np.random.uniform(10, 100, n_samples)

#formula: minutes = (3*distance) + small battery panalty +  noise
minutes = (3*distance) +(100-battery_levels)*0.05+ np.random.normal(0, 2, n_samples)

x = pd.DataFrame({
    "distance_km": distance,
    "battery_level": battery_levels
})
y=minutes

#2. Train a simple linear regression model
model = LinearRegression()
model.fit(x, y)

#3. Save the model

# path to the ml folder (the folder this script is in)
ML_DIR = Path(__file__).resolve().parent
MODEL_PATH = ML_DIR / "ride_time_model.pkl"

print("Training completed. Saving model...")
joblib.dump(model, MODEL_PATH)
print(f"Model saved as {MODEL_PATH}")
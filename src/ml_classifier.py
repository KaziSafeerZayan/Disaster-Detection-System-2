"""
Machine Learning Classifier for Water Body Segmentation from SAR Backscatter.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier

class FloodWaterClassifier:
    def __init__(self, n_estimators=100):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)

    def train(self, X_train: np.ndarray, y_train: np.ndarray):
        self.model.fit(X_train, y_train)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    def threshold_segmentation(self, sar_image_db: np.ndarray, threshold: float = -15.0) -> np.ndarray:
        return (sar_image_db < threshold).astype(np.uint8)
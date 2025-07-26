# In a new file: ml_payment_detector.py
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

class MLPaymentDetector:
    def __init__(self, model_path="./models/payment_classifier.joblib"):
        try:
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(model_path.replace("classifier", "vectorizer"))
            self.ml_available = True
        except:
            self.ml_available = False
    
    def extract_features(self, flow):
        # Extract text features from request
        url = flow.request.pretty_url.lower()
        content = flow.request.get_text().lower() if flow.request.content else ""
        headers = " ".join(f"{k.lower()}:{v.lower()}" for k, v in flow.request.headers.items())
        
        return f"{url} {headers} {content}"
    
    def is_payment(self, flow, threshold=0.6):
        if not self.ml_available:
            return None  # Fall back to rule-based approach
            
        features = self.extract_features(flow)
        X = self.vectorizer.transform([features])
        
        # Get probability of payment class
        proba = self.model.predict_proba(X)[0, 1]
        # Convert NumPy boolean to Python boolean with bool()
        return bool(proba > threshold)
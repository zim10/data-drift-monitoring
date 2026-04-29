import pickle
import boto3
import io
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from models import SessionLocal, PredictionRecord, create_tables
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time
import statistics
from datetime import datetime

# Prometheus Metrics
PREDICTION_COUNT = Counter(
    "churn_prediction_count", "Number of churn predictions made", ["result"]
)
PREDICTION_LATENCY = Histogram(
    "churn_prediction_latency_seconds", "Time taken for prediction",
    buckets=[0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5]
)
INPUT_FEATURE_GAUGE = Gauge(
    "churn_input_feature", "Input feature values", ["feature_name"]
)
FEATURE_DRIFT_GAUGE = Gauge(
    "churn_feature_drift", "Feature drift score", ["feature_name"]
)
PREDICTION_DISTRIBUTION = Histogram(
    "churn_prediction_distribution", "Prediction probability distribution",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# S3 Config
S3_BUCKET = "<your-s3-bucket-name>"   # ← replace this
MODEL_KEY = "model.pkl"

# Load model from S3
class MockModel:
    def predict_proba(self, X):
        n_samples = X.shape[0]
        probs = np.random.random((n_samples, 2))
        return probs / probs.sum(axis=1, keepdims=True)

try:
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=S3_BUCKET, Key=MODEL_KEY)
    model = pickle.load(io.BytesIO(response["Body"].read()))
    print("Model loaded from S3 successfully")
except Exception as e:
    print(f"Failed to load model: {e}. Using mock model.")
    model = MockModel()

# Baseline stats
BASELINE_STATS = {
    "tenure": {"mean": 32.4, "std": 24.6},
    "MonthlyCharges": {"mean": 64.8, "std": 30.1},
    "TotalCharges": {"mean": 2283.3, "std": 2266.8},
}

cumulative_stats = {
    f: {"values": [], "last_update": datetime.now()}
    for f in BASELINE_STATS.keys()
}

def update_feature_statistics(feature_name, value):
    stats = cumulative_stats[feature_name]
    stats["values"].append(value)
    if len(stats["values"]) > 1000:
        stats["values"] = stats["values"][-1000:]

    current_time = datetime.now()
    if (current_time - stats["last_update"]).total_seconds() > 60:
        current_mean = statistics.mean(stats["values"])
        current_std = statistics.stdev(stats["values"]) if len(stats["values"]) > 1 else 0
        mean_drift = abs(current_mean - BASELINE_STATS[feature_name]["mean"]) / BASELINE_STATS[feature_name]["std"]
        std_drift = abs(current_std - BASELINE_STATS[feature_name]["std"]) / BASELINE_STATS[feature_name]["std"]
        drift_score = (mean_drift + std_drift) / 2
        FEATURE_DRIFT_GAUGE.labels(feature_name=feature_name).set(drift_score)
        stats["last_update"] = current_time

class CustomerFeatures(BaseModel):
    gender: int
    SeniorCitizen: int
    Partner: int
    Dependents: int
    tenure: float
    PhoneService: int
    MultipleLines: int
    OnlineSecurity: int
    OnlineBackup: int
    DeviceProtection: int
    TechSupport: int
    StreamingTV: int
    StreamingMovies: int
    PaperlessBilling: int
    MonthlyCharges: float
    TotalCharges: float
    InternetService_DSL: int
    InternetService_Fiber_optic: int
    InternetService_No: int
    Contract_Month_to_month: int
    Contract_One_year: int
    Contract_Two_year: int
    PaymentMethod_Bank_transfer_automatic: int
    PaymentMethod_Credit_card_automatic: int
    PaymentMethod_Electronic_check: int
    PaymentMethod_Mailed_check: int

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scaler = MinMaxScaler()
large_cols = ["tenure", "MonthlyCharges", "TotalCharges"]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def preprocess_input(data: List[CustomerFeatures]):
    df = pd.DataFrame([item.dict() for item in data])
    for feature in BASELINE_STATS.keys():
        if feature in df.columns:
            mean_value = df[feature].mean()
            INPUT_FEATURE_GAUGE.labels(feature_name=feature).set(mean_value)
            update_feature_statistics(feature, mean_value)
    df[large_cols] = scaler.fit_transform(df[large_cols])
    return df.values

@app.on_event("startup")
def startup_db_client():
    try:
        create_tables()
        print("Database tables created")
    except Exception as e:
        print(f"DB error: {e}")

@app.post("/predict")
def predict(data: List[CustomerFeatures], db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        input_data = preprocess_input(data)
        predictions_proba = model.predict_proba(input_data)[:, 1]
        predictions = (predictions_proba >= 0.5).astype(int)

        for i, item in enumerate(data):
            db.add(PredictionRecord(**item.dict(), prediction=int(predictions[i])))
        db.commit()

        for prob in predictions_proba:
            PREDICTION_DISTRIBUTION.observe(prob)

        churn_count = sum(predictions)
        PREDICTION_COUNT.labels(result="churn").inc(churn_count)
        PREDICTION_COUNT.labels(result="non_churn").inc(len(predictions) - churn_count)
        PREDICTION_LATENCY.observe(time.time() - start_time)

        return {
            "predictions": predictions.tolist(),
            "probabilities": predictions_proba.tolist()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/drift")
def get_drift_metrics():
    return {
        f: FEATURE_DRIFT_GAUGE.labels(feature_name=f)._value.get()
        for f in BASELINE_STATS.keys()
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
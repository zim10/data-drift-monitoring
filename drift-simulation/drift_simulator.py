import requests
import pandas as pd
import numpy as np
import time
import random
from tqdm import tqdm

API_URL = "http://47.129.141.210:8000/predict"  # ← replace this with your new ec2 Public IPv4 address

df = pd.read_csv("WA_FnUseC_TelcoCustomerChurn.csv")

def preprocess_data(row):
    feature_map = {
        'gender': {'Female': 0, 'Male': 1},
        'Partner': {'Yes': 1, 'No': 0},
        'Dependents': {'Yes': 1, 'No': 0},
        'PhoneService': {'Yes': 1, 'No': 0},
        'MultipleLines': {'No': 0, 'Yes': 1, 'No phone service': 2},
        'OnlineSecurity': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'OnlineBackup': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'DeviceProtection': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'TechSupport': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'StreamingTV': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'StreamingMovies': {'No': 0, 'Yes': 1, 'No internet service': 2},
        'PaperlessBilling': {'Yes': 1, 'No': 0},
        'PaymentMethod': {
            'Electronic check': 1,
            'Mailed check': 0,
            'Bank transfer (automatic)': 0,
            'Credit card (automatic)': 0
        },
        'InternetService': {'DSL': 1, 'Fiber optic': 0, 'No': 0}
    }

    return {
        'gender': feature_map['gender'].get(row['gender'], 0),
        'SeniorCitizen': row['SeniorCitizen'],
        'Partner': feature_map['Partner'].get(row['Partner'], 0),
        'Dependents': feature_map['Dependents'].get(row['Dependents'], 0),
        'tenure': float(row['tenure']),
        'PhoneService': feature_map['PhoneService'].get(row['PhoneService'], 0),
        'MultipleLines': feature_map['MultipleLines'].get(row['MultipleLines'], 0),
        'OnlineSecurity': feature_map['OnlineSecurity'].get(row['OnlineSecurity'], 0),
        'OnlineBackup': feature_map['OnlineBackup'].get(row['OnlineBackup'], 0),
        'DeviceProtection': feature_map['DeviceProtection'].get(row['DeviceProtection'], 0),
        'TechSupport': feature_map['TechSupport'].get(row['TechSupport'], 0),
        'StreamingTV': feature_map['StreamingTV'].get(row['StreamingTV'], 0),
        'StreamingMovies': feature_map['StreamingMovies'].get(row['StreamingMovies'], 0),
        'PaperlessBilling': feature_map['PaperlessBilling'].get(row['PaperlessBilling'], 0),
        'MonthlyCharges': float(row['MonthlyCharges']),
        'TotalCharges': float(row['TotalCharges']) if row['TotalCharges'].strip() else 0.0,
        'InternetService_DSL': 1 if row['InternetService'] == 'DSL' else 0,
        'InternetService_Fiber_optic': 1 if row['InternetService'] == 'Fiber optic' else 0,
        'InternetService_No': 1 if row['InternetService'] == 'No' else 0,
        'Contract_Month_to_month': 1 if row['Contract'] == 'Month-to-month' else 0,
        'Contract_One_year': 1 if row['Contract'] == 'One year' else 0,
        'Contract_Two_year': 1 if row['Contract'] == 'Two year' else 0,
        'PaymentMethod_Bank_transfer_automatic': 1 if row['PaymentMethod'] == 'Bank transfer (automatic)' else 0,
        'PaymentMethod_Credit_card_automatic': 1 if row['PaymentMethod'] == 'Credit card (automatic)' else 0,
        'PaymentMethod_Electronic_check': 1 if row['PaymentMethod'] == 'Electronic check' else 0,
        'PaymentMethod_Mailed_check': 1 if row['PaymentMethod'] == 'Mailed check' else 0,
    }

def apply_drift(data, drift_type, intensity=0.2):
    drifted = data.copy()
    if drift_type == "feature_drift":
        drifted["MonthlyCharges"] *= (1 + intensity)
        drifted["tenure"] = drifted["tenure"] * (1 - intensity / 2)
    elif drift_type == "concept_drift":
        if random.random() < intensity:
            drifted["StreamingTV"] = 1
            drifted["StreamingMovies"] = 1
    elif drift_type == "seasonal_drift":
        if random.random() < intensity:
            drifted["Contract_Month_to_month"] = 1
            drifted["Contract_One_year"] = 0
            drifted["Contract_Two_year"] = 0
    return drifted

def send_batch(processed_data):
    try:
        response = requests.post(API_URL, json=processed_data)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {e}")

def simulate_data_drift():
    print("Phase 1: No drift (baseline)")
    for _ in tqdm(range(50)):
        sample = df.sample(10)
        data = [preprocess_data(row) for _, row in sample.iterrows()]
        send_batch(data)
        time.sleep(1)

    print("\nPhase 2: Gradual feature drift")
    for i in tqdm(range(100)):
        intensity = min(0.5, i * 0.005)
        sample = df.sample(10)
        data = [preprocess_data(row) for _, row in sample.iterrows()]
        drifted = [apply_drift(d, "feature_drift", intensity) for d in data]
        send_batch(drifted)
        time.sleep(1)

    print("\nPhase 3: Concept drift")
    for _ in tqdm(range(50)):
        sample = df.sample(10)
        data = [preprocess_data(row) for _, row in sample.iterrows()]
        drifted = [apply_drift(d, "concept_drift", 0.3) for d in data]
        send_batch(drifted)
        time.sleep(1)

    print("\nPhase 4: Back to normal")
    for _ in tqdm(range(50)):
        sample = df.sample(10)
        data = [preprocess_data(row) for _, row in sample.iterrows()]
        send_batch(data)
        time.sleep(1)

    print("\nSimulation complete!")

if __name__ == "__main__":
    simulate_data_drift()
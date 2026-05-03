"""
Model Drift Monitor using Evidently AI
Monitors data drift, target drift, and prediction drift.
"""

import pandas as pd
import numpy as np
import os
import sys
import json
from datetime import datetime
from evidently.dashboard import Dashboard
from evidently.tabs import DataDriftTab, CatTargetDriftTab, NumTargetDriftTab
from evidently.pipeline.column_mapping import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, ClassificationPreset

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_data(reference_path: str, current_path: str):
    """Load reference and current datasets."""
    reference_df = pd.read_csv(reference_path)
    current_df = pd.read_csv(current_path)

    print(f"Reference data: {len(reference_df)} rows")
    print(f"Current data: {len(current_df)} rows")

    return reference_df, current_df


def get_column_mapping() -> ColumnMapping:
    """Define column mapping for Evidently analysis."""
    mapping = ColumnMapping()

    # Define target column (for churn prediction)
    mapping.target = 'Churn'

    # Define prediction column (if available)
    mapping.prediction = 'prediction'

    # Numerical features
    mapping.numerical_features = [
        'tenure',
        'MonthlyCharges',
        'TotalCharges'
    ]

    # Categorical features
    mapping.categorical_features = [
        'gender',
        'SeniorCitizen',
        'Partner',
        'Dependents',
        'PhoneService',
        'MultipleLines',
        'InternetService',
        'OnlineSecurity',
        'OnlineBackup',
        'DeviceProtection',
        'TechSupport',
        'StreamingTV',
        'StreamingMovies',
        'Contract',
        'PaperlessBilling',
        'PaymentMethod'
    ]

    return mapping


def preprocess_for_drift(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess data for drift detection."""
    df = df.copy()

    # Drop customerID if present
    if 'customerID' in df.columns:
        df = df.drop('customerID', axis=1)

    # Convert TotalCharges to numeric
    if 'TotalCharges' in df.columns:
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
        df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].median())

    # Convert target to string for classification
    if 'Churn' in df.columns:
        df['Churn'] = df['Churn'].map({'Yes': 1, 'No': 0, 1: 1, 0: 0})
        df['Churn'] = df['Churn'].fillna(0).astype(int)

    # Convert SeniorCitizen to category
    if 'SeniorCitizen' in df.columns:
        df['SeniorCitizen'] = df['SeniorCitizen'].astype('category')

    return df


def run_data_drift_analysis(reference_df: pd.DataFrame, current_df: pd.DataFrame,
                            output_path: str = "model-drift/reports"):
    """Run data drift analysis using Evidently AI."""
    os.makedirs(output_path, exist_ok=True)

    # Preprocess data
    reference_df = preprocess_for_drift(reference_df)
    current_df = preprocess_for_drift(current_df)

    # Get column mapping
    mapping = get_column_mapping()

    # Filter to only include features that exist in both dataframes
    available_numerical = [f for f in mapping.numerical_features if f in reference_df.columns]
    available_categorical = [f for f in mapping.categorical_features if f in reference_df.columns]

    mapping.numerical_features = available_numerical
    mapping.categorical_features = available_categorical

    # Remove target from features if not in current
    if mapping.target not in current_df.columns:
        mapping.target = None

    # Create Data Drift Report
    print("\n📊 Running Data Drift Analysis...")

    data_drift_report = Report(metrics=[
        DataDriftPreset()
    ])

    data_drift_report.run(
        reference_data=reference_df,
        current_data=current_df,
        column_mapping=mapping
    )

    # Save report as JSON
    report_path = f"{output_path}/data_drift_report.json"
    data_drift_report.save_json(report_path)
    print(f"✅ Data drift report saved to {report_path}")

    # Get drift results
    result = data_drift_report.as_dict()

    # Extract drift metrics
    drift_detected = result['metrics'][0]['result']['drift_detected']
    drift_score = result['metrics'][0]['result']['drift_score']

    print(f"\n📈 Data Drift Results:")
    print(f"  Drift Detected: {'Yes' if drift_detected else 'No'}")
    print(f"  Drift Score: {drift_score:.4f}")

    # Show per-column drift
    if 'drift_by_columns' in result['metrics'][0]['result']:
        print("\n  Drift by Column:")
        for col, col_drift in result['metrics'][0]['result']['drift_by_columns'].items():
            if isinstance(col_drift, dict) and 'drift_score' in col_drift:
                status = "⚠️" if col_drift['drift_detected'] else "✅"
                print(f"    {status} {col}: {col_drift['drift_score']:.4f}")

    return result


def run_target_drift_analysis(reference_df: pd.DataFrame, current_df: pd.DataFrame,
                               output_path: str = "model-drift/reports"):
    """Run target drift analysis."""
    os.makedirs(output_path, exist_ok=True)

    # Preprocess data
    reference_df = preprocess_for_drift(reference_df)
    current_df = preprocess_for_drift(current_df)

    mapping = get_column_mapping()

    # Check if target exists
    if mapping.target not in reference_df.columns or mapping.target not in current_df.columns:
        print("⚠️ Target column not found, skipping target drift analysis")
        return None

    print("\n📊 Running Target Drift Analysis...")

    target_drift_report = Report(metrics=[
        TargetDriftPreset()
    ])

    target_drift_report.run(
        reference_data=reference_df,
        current_data=current_df,
        column_mapping=mapping
    )

    # Save report
    report_path = f"{output_path}/target_drift_report.json"
    target_drift_report.save_json(report_path)
    print(f"✅ Target drift report saved to {report_path}")

    result = target_drift_report.as_dict()
    return result


def run_prediction_drift_analysis(reference_df: pd.DataFrame, current_df: pd.DataFrame,
                                   predictions_ref: list = None, predictions_curr: list = None,
                                   output_path: str = "model-drift/reports"):
    """Run prediction drift analysis."""
    os.makedirs(output_path, exist_ok=True)

    print("\n📊 Running Prediction Drift Analysis...")

    # If we have predictions, add them to the dataframes
    if predictions_ref is not None and predictions_curr is None:
        # Use actual data as current if no separate predictions
        predictions_curr = predictions_ref[len(predictions_ref)//2:]

    # For now, just use data drift on target as proxy
    reference_df = preprocess_for_drift(reference_df)
    current_df = preprocess_for_drift(current_df)

    mapping = get_column_mapping()

    # Create classification report
    if 'prediction' in reference_df.columns and 'prediction' in current_df.columns:
        classification_report = Report(metrics=[
            ClassificationPreset()
        ])

        classification_report.run(
            reference_data=reference_df,
            current_data=current_df,
            column_mapping=mapping
        )

        report_path = f"{output_path}/classification_report.json"
        classification_report.save_json(report_path)
        print(f"✅ Classification report saved to {report_path}")

        return classification_report.as_dict()

    return None


def generate_html_report(reference_df: pd.DataFrame, current_df: pd.DataFrame,
                         output_path: str = "model-drift/reports"):
    """Generate interactive HTML dashboard."""
    os.makedirs(output_path, exist_ok=True)

    # Preprocess data
    reference_df = preprocess_for_drift(reference_df)
    current_df = preprocess_for_drift(current_df)

    mapping = get_column_mapping()

    # Filter available features
    available_numerical = [f for f in mapping.numerical_features if f in reference_df.columns]
    available_categorical = [f for f in mapping.categorical_features if f in reference_df.columns]
    mapping.numerical_features = available_numerical
    mapping.categorical_features = available_categorical

    if mapping.target not in current_df.columns:
        mapping.target = None

    # Create dashboard with multiple tabs
    dashboard = Dashboard(tabs=[
        DataDriftTab(),
        CatTargetDriftTab(),
        NumTargetDriftTab()
    ])

    dashboard.calculate(
        reference_data=reference_df,
        current_data=current_df,
        column_mapping=mapping
    )

    # Save dashboard as HTML
    dashboard_path = f"{output_path}/drift_dashboard.html"
    dashboard.save(dashboard_path)
    print(f"✅ Interactive dashboard saved to {dashboard_path}")

    return dashboard_path


def main():
    """Main function to run drift monitoring."""
    print("=" * 60)
    print("🔍 Model Drift Monitor using Evidently AI")
    print("=" * 60)

    # Paths
    reference_path = "model-drift/data/reference.csv"
    current_path = "model-drift/data/current.csv"
    output_path = "model-drift/reports"

    # Check if data exists
    if not os.path.exists(reference_path) or not os.path.exists(current_path):
        print(f"❌ Data files not found!")
        print(f"   Expected: {reference_path} and {current_path}")
        print(f"   Run dataset-upload.py first to download and prepare data")
        return

    # Load data
    print("\n📥 Loading data...")
    reference_df, current_df = load_data(reference_path, current_path)

    # Run analyses
    data_drift_result = run_data_drift_analysis(reference_df, current_df, output_path)
    target_drift_result = run_target_drift_analysis(reference_df, current_df, output_path)

    # Generate HTML dashboard
    generate_html_report(reference_df, current_df, output_path)

    # Summary
    print("\n" + "=" * 60)
    print("📋 DRIFT MONITORING SUMMARY")
    print("=" * 60)

    if data_drift_result:
        drift_detected = data_drift_result['metrics'][0]['result']['drift_detected']
        drift_score = data_drift_result['metrics'][0]['result']['drift_score']

        print(f"\n🔹 Data Drift Status: {'⚠️ DRIFT DETECTED' if drift_detected else '✅ STABLE'}")
        print(f"🔹 Drift Score: {drift_score:.4f}")
        print(f"\n📁 Reports saved to: {output_path}/")
        print(f"   - data_drift_report.json")
        print(f"   - target_drift_report.json")
        print(f"   - drift_dashboard.html")

    print("\n✅ Drift monitoring complete!")


if __name__ == "__main__":
    main()
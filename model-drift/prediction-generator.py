"""
Prediction Generator
Generates predictions from the ML model and saves results for drift monitoring.
"""

import boto3
import pandas as pd
import pickle
import numpy as np
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_model_from_s3(bucket_name: str, model_key: str = "model.pkl"):
    """Load the ML model from S3."""
    s3_client = boto3.client('s3')

    try:
        # Download model to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            s3_client.download_fileobj(bucket_name, model_key, tmp)
            tmp_path = tmp.name

        with open(tmp_path, 'rb') as f:
            model = pickle.load(f)

        os.unlink(tmp_path)
        print("✅ Model loaded from S3")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess telco customer churn data for prediction."""
    df = df.copy()

    # Drop customerID as it's not a feature
    if 'customerID' in df.columns:
        df = df.drop('customerID', axis=1)

    # Remove target column if present
    if 'Churn' in df.columns:
        df = df.drop('Churn', axis=1)

    # Convert TotalCharges to numeric FIRST (before categorical)
    if 'TotalCharges' in df.columns:
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

    # Handle ALL remaining categorical columns - convert to numeric
    for col in df.columns:
        if df[col].dtype == 'object':
            # Convert to categorical codes
            df[col] = pd.Categorical(df[col]).codes

    # Convert ALL columns to numeric, fill NaN with 0
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


def generate_predictions(model, df: pd.DataFrame) -> np.ndarray:
    """Generate predictions from the model."""
    try:
        # Remove target column if present
        if 'Churn' in df.columns:
            df = df.drop('Churn', axis=1)

        # Convert to numpy array to bypass feature name checking
        X = df.values

        predictions = model.predict(X)
        probabilities = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else None

        return predictions, probabilities
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return None, None


def save_predictions(predictions: np.ndarray, probabilities: np.ndarray,
                     original_df: pd.DataFrame, output_path: str):
    """Save predictions along with original data."""
    result_df = original_df.copy()

    if 'customerID' not in result_df.columns:
        result_df.insert(0, 'customerID', range(len(result_df)))

    result_df['prediction'] = predictions
    if probabilities is not None:
        result_df['probability'] = probabilities

    result_df.to_csv(output_path, index=False)
    print(f"✅ Saved predictions to {output_path}")


def main():
    # Configuration
    BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'your-bucket-name')
    INPUT_DATA_PATH = "model-drift/data/current.csv"
    PREDICTIONS_OUTPUT_PATH = "model-drift/data/predictions.csv"

    # Create output directory
    os.makedirs("model-drift/data", exist_ok=True)

    # Load model
    model = load_model_from_s3(BUCKET_NAME)
    if model is None:
        # Fallback: try loading local model
        if os.path.exists("model.pkl"):
            with open("model.pkl", 'rb') as f:
                model = pickle.load(f)
            print("✅ Model loaded from local file")
        else:
            print("❌ No model available")
            return

    # Load dataset
    if not os.path.exists(INPUT_DATA_PATH):
        print(f"❌ Input data not found: {INPUT_DATA_PATH}")
        print("Run dataset-upload.py first to download data")
        return

    df = pd.read_csv(INPUT_DATA_PATH)
    print(f"Loaded {len(df)} records from {INPUT_DATA_PATH}")

    # Preprocess
    df_processed = preprocess_data(df)

    # Generate predictions
    predictions, probabilities = generate_predictions(model, df_processed)

    if predictions is not None:
        # Save predictions
        save_predictions(predictions, probabilities, df, PREDICTIONS_OUTPUT_PATH)

        # Print summary
        print(f"\n📊 Prediction Summary:")
        print(f"  Total predictions: {len(predictions)}")
        print(f"  Churn predicted: {sum(predictions)} ({sum(predictions)/len(predictions)*100:.1f}%)")
        print(f"  No churn: {len(predictions) - sum(predictions)} ({(len(predictions) - sum(predictions))/len(predictions)*100:.1f}%)")

        if probabilities is not None:
            print(f"  Avg probability: {np.mean(probabilities):.3f}")

    print("\n✅ Prediction generation complete!")


if __name__ == "__main__":
    main()
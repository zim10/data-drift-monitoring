import os
import boto3
import pandas as pd
import psycopg2
import io
from sqlalchemy import create_engine
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.metrics import ColumnDriftMetric, ColumnSummaryMetric
from datetime import datetime

# S3 configuration (can be overridden with env vars)
S3_BUCKET = os.environ.get("S3_BUCKET", "customer-churn-model-bucket-25ae6be")
S3_FILE_KEY = os.environ.get("S3_FILE_KEY", "my_dataset.csv")  # Reference dataset
REPORT_OUTPUT_DIR = "reports"

# Database configuration (defaults to localhost for local runs, postgres for Docker)
DB_USER = os.environ.get("DB_USER", "my_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "my_password")
DB_NAME = os.environ.get("DB_NAME", "my_db")
DB_HOST = os.environ.get("DB_HOST", "localhost")  # Use "postgres" in Docker, "localhost" locally

def create_db_connection():
    """Create a connection to the PostgreSQL database"""
    try:
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        raise

def fetch_postgres_data(engine):
    """Fetch prediction records from PostgreSQL database"""
    try:
        query = "SELECT * FROM predictions"
        df = pd.read_sql(query, engine)
        print(f"Retrieved {len(df)} records from PostgreSQL")
        return df
    except Exception as e:
        print(f"Error fetching data from PostgreSQL: {str(e)}")
        raise

def fetch_s3_data():
    """Fetch reference dataset from S3 bucket"""
    try:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_KEY)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))
        print(f"Retrieved reference dataset from S3 with {len(df)} records")
        return df
    except Exception as e:
        print(f"Error fetching data from S3: {str(e)}")
        raise

def prepare_datasets(current_df, reference_df):
    """Prepare both datasets for comparison by aligning columns"""
    # Ensure column alignment, drop any columns that don't exist in both datasets
    common_columns = list(set(current_df.columns).intersection(set(reference_df.columns)))

    # Remove 'id' and 'prediction' from comparison if they exist
    for col in ['id', 'prediction']:
        if col in common_columns:
            common_columns.remove(col)

    print(f"Comparing {len(common_columns)} common columns")

    # Get the prepared dataframes
    current_prep = current_df[common_columns].copy()
    reference_prep = reference_df[common_columns].copy()

    # Convert string columns to numeric where possible (e.g., "Yes"/"No" -> 1/0)
    for col in common_columns:
        # Try to convert reference column to numeric if it's string/object
        if reference_prep[col].dtype == 'object':
            # Try mapping common string values
            unique_ref = set(reference_prep[col].dropna().unique())
            if unique_ref <= {'Yes', 'No', 'True', 'False', '1', '0'}:
                # Map to numeric
                ref_mapped = reference_prep[col].map({'Yes': 1, 'No': 0, 'True': 1, 'False': 0, '1': 1, '0': 0})
                if current_prep[col].dtype == 'object':
                    current_prep[col] = current_prep[col].map({'Yes': 1, 'No': 0, 'True': 1, 'False': 0, '1': 1, '0': 0})
                reference_prep[col] = ref_mapped

    # Convert all columns to native Python types for Evidently compatibility
    # This handles StringDtype, nullable types, etc.
    for col in common_columns:
        current_prep[col] = current_prep[col].apply(lambda x: str(x) if pd.notna(x) else "")
        reference_prep[col] = reference_prep[col].apply(lambda x: str(x) if pd.notna(x) else "")

    # Recreate DataFrames with plain types
    current_prep = pd.DataFrame(current_prep, columns=common_columns)
    reference_prep = pd.DataFrame(reference_prep, columns=common_columns)

    return current_prep, reference_prep

def generate_drift_report(current_data, reference_data, report_name="drift_report"):
    """Generate Evidently data drift report"""
    try:
        # Create directory for reports if it doesn't exist
        os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
        
        # Format current timestamp for the report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"{REPORT_OUTPUT_DIR}/{report_name}_{timestamp}.html"
        
        # Prepare data for comparison
        current_data_prep, reference_data_prep = prepare_datasets(current_data, reference_data)
        
        # Create and run the report
        report = Report(metrics=[
            DataDriftPreset(),
            DataQualityPreset()
])
        
        report.run(reference_data=reference_data_prep, current_data=current_data_prep)
        report.save_html(report_path)
        
        print(f"Drift report saved to {report_path}")
        return report_path
    except Exception as e:
        print(f"Error generating drift report: {str(e)}")
        raise

def upload_report_to_s3(report_path, s3_key=None):
    """Upload generated report to S3 bucket"""
    try:
        s3 = boto3.client("s3")
        if s3_key is None:
            s3_key = f"reports/{os.path.basename(report_path)}"
        
        s3.upload_file(report_path, S3_BUCKET, s3_key)
        print(f"Report uploaded to S3: s3://{S3_BUCKET}/{s3_key}")
    except Exception as e:
        print(f"Error uploading report to S3: {str(e)}")

def generate_feature_drift_reports(current_data, reference_data):
    """Generate individual feature drift reports for important features"""
    try:
        os.makedirs(f"{REPORT_OUTPUT_DIR}/features", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define important features to monitor individually
        important_features = [
            "tenure", "MonthlyCharges", "TotalCharges", 
            "Contract_Month_to_month", "InternetService_Fiber_optic"
        ]
        
        # Create individual reports for each important feature
        for feature in important_features:
            if feature in current_data.columns and feature in reference_data.columns:
                report = Report(metrics=[
                    ColumnDriftMetric(column_name=feature),
                    ColumnSummaryMetric(column_name=feature)
                ])
                
                current_data_prep, reference_data_prep = prepare_datasets(current_data, reference_data)
                report.run(reference_data=reference_data_prep, current_data=current_data_prep)
                
                report_path = f"{REPORT_OUTPUT_DIR}/features/{feature}_drift_{timestamp}.html"
                report.save_html(report_path)
                
                print(f"Feature drift report for '{feature}' saved to {report_path}")
                upload_report_to_s3(report_path, f"reports/features/{feature}_drift_{timestamp}.html")
    except Exception as e:
        print(f"Error generating feature drift reports: {str(e)}")

def main():
    """Main function to run monitoring"""
    try:
        print("Starting model and data drift monitoring...")
        
        # Connect to the database
        engine = create_db_connection()
        
        # Fetch data from both sources
        current_df = fetch_postgres_data(engine)
        reference_df = fetch_s3_data()
        
        # Generate main drift report
        report_path = generate_drift_report(current_df, reference_df)
        
        # Upload report to S3
        upload_report_to_s3(report_path)
        
        # Generate feature-specific drift reports
        generate_feature_drift_reports(current_df, reference_df)
        
        print("Monitoring completed successfully")
    except Exception as e:
        print(f"Error in monitoring process: {str(e)}")

if __name__ == "__main__":
    main()

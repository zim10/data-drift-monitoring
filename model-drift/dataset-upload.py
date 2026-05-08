import boto3

# Define the second S3 bucket details
dataset_bucket = "your bucket name"  # Different S3 bucket
s3_dataset_path = "my_dataset.csv"  # Path in S3
local_dataset_path = "your dataset local path"  # Local file path

# Create an S3 client
s3 = boto3.client("s3")

# Upload the dataset file
s3.upload_file(local_dataset_path, dataset_bucket, s3_dataset_path)

print(f"Dataset uploaded successfully to s3://{dataset_bucket}/{s3_dataset_path}")




# """
# Dataset Upload Script
# Uploads reference and current datasets to S3 for model drift monitoring.
# """

# import boto3
# import pandas as pd
# import os
# import sys

# # Add parent directory to path for imports
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# def upload_dataset_to_s3(bucket_name: str, local_file: str, s3_key: str):
#     """Upload a dataset file to S3."""
#     s3_client = boto3.client('s3')

#     try:
#         s3_client.upload_file(local_file, bucket_name, s3_key)
#         print(f"✅ Uploaded {local_file} to s3://{bucket_name}/{s3_key}")
#         return True
#     except Exception as e:
#         print(f"❌ Failed to upload {local_file}: {e}")
#         return False


# def download_dataset_from_url(url: str, local_path: str):
#     """Download dataset from URL."""
#     import urllib.request

#     if os.path.exists(local_path):
#         print(f"Dataset already exists at {local_path}")
#         return True

#     try:
#         urllib.request.urlretrieve(url, local_path)
#         print(f"✅ Downloaded dataset to {local_path}")
#         return True
#     except Exception as e:
#         print(f"❌ Failed to download dataset: {e}")
#         return False


# def main():
#     # Configuration
#     BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'your-bucket-name')
#     DATASET_URL = "https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Data/Telco-Customer-Churn.csv"
#     LOCAL_DATA_DIR = "model-drift/data"
#     REFERENCE_DATA_KEY = "data/reference.csv"
#     CURRENT_DATA_KEY = "data/current.csv"

#     # Create local data directory
#     os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

#     # Download dataset
#     local_dataset = f"{LOCAL_DATA_DIR}/WA_FnUseC_TelcoCustomerChurn.csv"
#     if not download_dataset_from_url(DATASET_URL, local_dataset):
#         return

#     # Load and split dataset
#     df = pd.read_csv(local_dataset)

#     # Use first 70% as reference data (baseline)
#     reference_size = int(len(df) * 0.7)
#     reference_df = df.iloc[:reference_size]
#     current_df = df.iloc[reference_size:]

#     # Save reference and current datasets
#     reference_path = f"{LOCAL_DATA_DIR}/reference.csv"
#     current_path = f"{LOCAL_DATA_DIR}/current.csv"

#     reference_df.to_csv(reference_path, index=False)
#     current_df.to_csv(current_path, index=False)

#     print(f"Reference dataset: {len(reference_df)} rows saved to {reference_path}")
#     print(f"Current dataset: {len(current_df)} rows saved to {current_path}")

#     # Upload to S3
#     upload_dataset_to_s3(BUCKET_NAME, reference_path, REFERENCE_DATA_KEY)
#     upload_dataset_to_s3(BUCKET_NAME, current_path, CURRENT_DATA_KEY)

#     print("\n✅ Dataset upload complete!")


# if __name__ == "__main__":
#     main()
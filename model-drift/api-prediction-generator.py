import requests
import json
import random
import pandas as pd
import time
import argparse
from sqlalchemy import create_engine

# Configuration
API_ENDPOINT = "http://localhost:8000/predict"  # Adjust if your API is on a different host or port
DB_CONFIG = {
    "user": "my_user",
    "password": "my_password",
    "host": "postgres",  # Change to your EC2's public IP if accessing from outside
    "port": "5432",
    "database": "my_db"
}

def generate_customer_data(num_samples=10):
    """Generate random customer data for churn prediction"""
    customers = []

    for _ in range(num_samples):
        # Binary features (0 or 1)
        gender = random.randint(0, 1)
        senior_citizen = random.randint(0, 1)
        partner = random.randint(0, 1)
        dependents = random.randint(0, 1)
        phone_service = random.randint(0, 1)
        multiple_lines = random.randint(0, 1) if phone_service == 1 else 0
        online_security = random.randint(0, 1)
        online_backup = random.randint(0, 1)
        device_protection = random.randint(0, 1)
        tech_support = random.randint(0, 1)
        streaming_tv = random.randint(0, 1)
        streaming_movies = random.randint(0, 1)
        paperless_billing = random.randint(0, 1)

        # Continuous features
        tenure = round(random.uniform(0, 72), 1)  # 0-72 months
        monthly_charges = round(random.uniform(20, 120), 2)  # $20-$120
        total_charges = round(tenure * monthly_charges * random.uniform(0.9, 1.1), 2)  # Approx tenure * monthly with some variation

        # Create one-hot encoded features
        # Internet Service (choose one)
        internet_options = ["DSL", "Fiber_optic", "No"]
        internet_choice = random.choice(internet_options)
        internet_service_dsl = 1 if internet_choice == "DSL" else 0
        internet_service_fiber_optic = 1 if internet_choice == "Fiber_optic" else 0
        internet_service_no = 1 if internet_choice == "No" else 0

        # Contract (choose one)
        contract_options = ["Month_to_month", "One_year", "Two_year"]
        contract_choice = random.choice(contract_options)
        contract_month_to_month = 1 if contract_choice == "Month_to_month" else 0
        contract_one_year = 1 if contract_choice == "One_year" else 0
        contract_two_year = 1 if contract_choice == "Two_year" else 0

        # Payment Method (choose one)
        payment_options = ["Bank_transfer_automatic", "Credit_card_automatic", "Electronic_check", "Mailed_check"]
        payment_choice = random.choice(payment_options)
        payment_bank_transfer = 1 if payment_choice == "Bank_transfer_automatic" else 0
        payment_credit_card = 1 if payment_choice == "Credit_card_automatic" else 0
        payment_electronic_check = 1 if payment_choice == "Electronic_check" else 0
        payment_mailed_check = 1 if payment_choice == "Mailed_check" else 0

        customer = {
            "gender": gender,
            "SeniorCitizen": senior_citizen,
            "Partner": partner,
            "Dependents": dependents,
            "tenure": tenure,
            "PhoneService": phone_service,
            "MultipleLines": multiple_lines,
            "OnlineSecurity": online_security,
            "OnlineBackup": online_backup,
            "DeviceProtection": device_protection,
            "TechSupport": tech_support,
            "StreamingTV": streaming_tv,
            "StreamingMovies": streaming_movies,
            "PaperlessBilling": paperless_billing,
            "MonthlyCharges": monthly_charges,
            "TotalCharges": total_charges,
            "InternetService_DSL": internet_service_dsl,
            "InternetService_Fiber_optic": internet_service_fiber_optic,
            "InternetService_No": internet_service_no,
            "Contract_Month_to_month": contract_month_to_month,
            "Contract_One_year": contract_one_year,
            "Contract_Two_year": contract_two_year,
            "PaymentMethod_Bank_transfer_automatic": payment_bank_transfer,
            "PaymentMethod_Credit_card_automatic": payment_credit_card,
            "PaymentMethod_Electronic_check": payment_electronic_check,
            "PaymentMethod_Mailed_check": payment_mailed_check
        }

        customers.append(customer)

    return customers

def make_prediction_request(data):
    """Send prediction request to the FastAPI endpoint"""
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(API_ENDPOINT, data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error making prediction: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while making prediction request: {str(e)}")
        return None

def verify_database_entries(num_expected):
    """Verify that entries were added to the database"""
    try:
        connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string)

        query = "SELECT COUNT(*) FROM predictions"
        result = pd.read_sql(query, engine)
        count = result.iloc[0, 0]

        print(f"Database verification: Found {count} records in predictions table")

        if count >= num_expected:
            print("Verification successful!")
        else:
            print(f"Expected at least {num_expected} records, but found {count}")

        # Get most recent entries
        recent_query = "SELECT * FROM predictions ORDER BY id DESC LIMIT 5"
        recent_records = pd.read_sql(recent_query, engine)
        print("\nMost recent prediction records:")
        print(recent_records)

        return count
    except Exception as e:
        print(f"Error verifying database entries: {str(e)}")
        return -1

def main():
    parser = argparse.ArgumentParser(description="Generate predictions and store in PostgreSQL")
    parser.add_argument("--num-samples", type=int, default=10,
                        help="Number of customer samples to generate (default: 10)")
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Batch size for API requests (default: 5)")
    parser.add_argument("--api-host", type=str, default="localhost",
                        help="Hostname/IP where the FastAPI service is running (default: localhost)")
    parser.add_argument("--api-port", type=int, default=8000,
                        help="Port where the FastAPI service is running (default: 8000)")
    parser.add_argument("--db-host", type=str, default="5432",
                        help="Hostname/IP where PostgreSQL is running (default: localhost)")

    args = parser.parse_args()

    # Update configuration based on arguments
    global API_ENDPOINT
    API_ENDPOINT = f"http://{args.api_host}:{args.api_port}/predict"
    DB_CONFIG["host"] = args.db_host

    print(f"=== Churn Prediction Generator ===")
    print(f"API Endpoint: {API_ENDPOINT}")
    print(f"Database Host: {DB_CONFIG['host']}")
    print(f"Generating {args.num_samples} customer records...")

    # Record starting count
    starting_count = verify_database_entries(0)
    if starting_count == -1:
        print("Cannot connect to database. Please check your connection settings.")
        return

    # Generate data and make predictions
    customers = generate_customer_data(args.num_samples)
    print(f"Generated {len(customers)} customer profiles")

    # Process in batches
    total_predictions = 0
    batch_size = min(args.batch_size, args.num_samples)

    for i in range(0, len(customers), batch_size):
        batch = customers[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1} with {len(batch)} customers...")

        result = make_prediction_request(batch)
        if result and "predictions" in result:
            total_predictions += len(result["predictions"])
            print(f"Batch predictions: {result['predictions']}")

        # Small delay to avoid overwhelming the API
        time.sleep(0.5)

    print(f"\nProcess completed. Made predictions for {total_predictions} customers.")

    # Verify final count
    final_count = verify_database_entries(starting_count + total_predictions)
    added_records = final_count - starting_count

    print(f"\nSummary:")
    print(f"- Starting record count: {starting_count}")
    print(f"- Attempted to add: {args.num_samples}")
    print(f"- Successfully added: {added_records}")
    print(f"- Final record count: {final_count}")

if __name__ == "__main__":
    main()
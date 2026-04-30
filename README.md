# Data Drift Monitoring System

A production-ready data drift monitoring system for a **Customer Churn Prediction** ML model. Detects and visualizes feature drift, concept drift, and seasonal drift in real time using FastAPI, Prometheus, Grafana, and AWS.

---

## What is Data Drift?

When a model is trained, it learns from data at a specific point in time. Over time, real-world data changes — causing the model to silently degrade in performance. This system detects that change **before it impacts business decisions**.

### 3 Types of Drift Monitored

| Type | Description | Example |
|---|---|---|
| **Feature Drift** | Input data distribution changes | Monthly charges increase over time |
| **Concept Drift** | Relationship between features and outcome changes | Streaming users now churn more |
| **Seasonal Drift** | Patterns shift with time or season | More month-to-month contracts |

---

## Architecture

```
Real Users → FastAPI App → ML Model (from S3) → Predictions
                 ↓
           Prometheus         (collects metrics every 5s)
                 ↓
             Grafana           (visualizes drift trends)
                 ↓
           PostgreSQL          (stores prediction history)

All services run on AWS EC2 via Docker Compose
Infrastructure provisioned with Pulumi
```

---

## Tech Stack

| Tool | Purpose |
|---|---|
| **FastAPI** | Serves ML model as REST API |
| **Prometheus** | Collects and stores metrics |
| **Grafana** | Visualizes drift as dashboards |
| **PostgreSQL** | Stores prediction history |
| **Docker Compose** | Runs all services together |
| **AWS EC2** | Cloud server to host everything |
| **AWS S3** | Stores the trained ML model |
| **Pulumi** | Provisions AWS infrastructure with Python |

---

## Project Structure

```
data-drift-monitoring/
├── fastapi-app/
│   ├── main.py              # FastAPI app with Prometheus metrics
│   ├── models.py            # PostgreSQL models
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Container for FastAPI app
├── drift-simulation/
│   ├── drift_simulator.py   # Simulates 4 phases of data drift
│   └── requirements.txt     # Simulator dependencies
├── infrastructure/
│   ├── __main__.py          # Pulumi AWS infrastructure code
│   ├── Pulumi.yaml          # Pulumi project config
│   └── requirements.txt     # Pulumi dependencies
├── monitoring/
│   └── prometheus.yml       # Prometheus scrape config
├── docker-compose.yml       # Runs all 4 containers
├── CLAUDE.md                # Claude Code context file
├── .gitignore
└── README.md
```

---

## Prerequisites

- AWS Account with Access Key and Secret Key
- Docker Hub Account
- Python 3.8+
- Pulumi CLI installed
- AWS CLI installed

---

## Getting Started

### Step 1 — Clone the Repo

```bash
git clone https://github.com/your-username/data-drift-monitoring.git
cd data-drift-monitoring
```

### Step 2 — Set Up AWS Infrastructure

```bash
cd infrastructure
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure AWS
aws configure

# Create SSH key pair
aws ec2 create-key-pair \
  --key-name key-pair-poridhi-poc \
  --query 'KeyMaterial' \
  --output text > key-pair-poridhi-poc.pem
chmod 400 key-pair-poridhi-poc.pem

# Deploy infrastructure
pulumi up --yes
```

> Note down the **EC2 Public IP** and **S3 Bucket Name** from the output!

### Step 3 — Upload ML Model to S3

```bash
cd ..
curl -o model.pkl https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Model/logistic_regression_model.pkl
pip install boto3
# Create s3_model_deploy.py with your bucket name and run:
python3 s3_model_deploy.py
```

### Step 4 — Set Up IAM Permissions

- Create IAM Policy `S3ModelAccessPolicy` with S3 read/write access
- Create IAM Role `EC2S3AccessRole` and attach the policy
- Attach the role to your EC2 instance

### Step 5 — Build and Push Docker Image

```bash
cd fastapi-app
# Update S3_BUCKET in main.py with your bucket name
docker build -t churn-prediction-app .
docker tag churn-prediction-app:latest <your-dockerhub-username>/churn-prediction-app:latest
docker push <your-dockerhub-username>/churn-prediction-app:latest
```

### Step 6 — Deploy on EC2

```bash
# SSH into EC2
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-PUBLIC-IP>

# Install Docker and Docker Compose
sudo apt update && sudo apt install -y docker-ce docker-compose

# Clone repo and run
git clone https://github.com/your-username/data-drift-monitoring.git
cd data-drift-monitoring
docker-compose up -d

# Verify all 4 containers are running
docker ps
```

### Step 7 — Run Drift Simulator

```bash
# On Poridhi server (not EC2)
cd drift-simulation
pip install -r requirements.txt

# Download dataset
curl -o WA_FnUseC_TelcoCustomerChurn.csv \
  https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Data/Telco-Customer-Churn.csv

# Update EC2 IP in drift_simulator.py then run:
python3 drift_simulator.py
```

### Step 8 — Visualize in Grafana

1. Open `http://<EC2-PUBLIC-IP>:3000` → Login: `admin/admin`
2. Go to **Settings → Data Sources → Add Prometheus**
3. URL: `http://<EC2-PUBLIC-IP>:9090` → Save & Test
4. Create dashboard with these queries:

| Panel | Prometheus Query |
|---|---|
| Feature Drift Score | `churn_feature_drift` |
| Total Predictions | `churn_prediction_count_total` |
| API Latency | `churn_prediction_latency_seconds` |
| Input Feature Values | `churn_input_feature` |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict` | Make churn predictions |
| GET | `/drift` | Get current drift scores |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/docs` | Swagger UI |

---

## Services & Ports

| Service | Port | URL |
|---|---|---|
| FastAPI | 8000 | `http://<EC2-IP>:8000/docs` |
| Prometheus | 9090 | `http://<EC2-IP>:9090` |
| Grafana | 3000 | `http://<EC2-IP>:3000` |
| PostgreSQL | 5432 | Internal only |

---

## Drift Simulation Phases

| Phase | What Happens | Batches |
|---|---|---|
| Phase 1 | Baseline — no drift | 50 |
| Phase 2 | Gradual feature drift — charges increase | 100 |
| Phase 3 | Concept drift — behavior patterns change | 50 |
| Phase 4 | Back to normal | 50 |

---

## Prometheus Metrics Tracked

| Metric | Description |
|---|---|
| `churn_prediction_count` | Number of churn vs non-churn predictions |
| `churn_prediction_latency_seconds` | API response time |
| `churn_input_feature` | Current values of key input features |
| `churn_feature_drift` | Drift score vs baseline |
| `churn_prediction_distribution` | Distribution of prediction probabilities |

---

## Roadmap

- [x] Phase 1 — Basic drift monitoring (FastAPI + Prometheus + Grafana)
- [ ] Phase 2 — Model drift detection
- [ ] Phase 3 — Automated alerting in Grafana
- [ ] Phase 4 — Automated retraining trigger
- [ ] Phase 5 — CI/CD pipeline

---

## Important Notes

- Never push `.pem` files, `.env`, `model.pkl`, or `*.csv` to GitHub
- Always add sensitive files to `.gitignore` before first commit
- `s3_model_deploy.py` contains your bucket name — never push it

---

## Conclusion

This system provides a robust framework for maintaining ML model reliability in production. By leveraging Prometheus for metrics collection and Grafana for visualization, it enables proactive model maintenance rather than reactive fixes after business impact has occurred.

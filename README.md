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
│   ├── models.py            # PostgreSQL models (SQLAlchemy)
│   └── Dockerfile           # Container for FastAPI app
├── drift-simulation/
│   └── drift_simulator.py   # Simulates 4 phases of data drift
├── infrastructure/
│   ├── __main__.py          # Pulumi AWS infrastructure code
│   ├── Pulumi.yaml          # Pulumi project config
│   ├── Pulumi.dev.yaml      # Pulumi dev stack config
│   └── requirements.txt     # Pulumi specific dependencies
├── monitoring/
│   └── prometheus.yml       # Prometheus scrape config
├── docker-compose.yml       # Runs all 4 containers together
├── requirements.txt         # ONE root level requirements file
├── CLAUDE.md                # Claude Code context file
├── .gitignore
└── README.md
```

---

## ⚠️ My current Server 

Every session gives me **fresh AWS credentials and a fresh AWS environment**. EC2, S3, and key pairs are all gone each session. I Follow the full setup below every time.

---

## Getting Started

### Phase 1 — Install Tools

```bash
# Install Python venv
sudo apt update && sudo apt install python3-venv -y

# Clone repo
git clone https://github.com/zim10/data-drift-monitoring.git
cd data-drift-monitoring

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install project packages
pip install -r requirements.txt

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version   # verify

# Install Pulumi
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin
pulumi version  # verify
```

### Phase 2 — Configure AWS and Deploy Infrastructure

```bash
# Configure AWS credentials
aws configure
# Enter: Access Key, Secret Key, region: us-east-1, format: json

# Verify credentials
aws sts get-caller-identity

# Go to infrastructure folder
cd infrastructure

# Create SSH key pair (fresh every Poridhi session!)
aws ec2 create-key-pair \
  --key-name key-pair-poridhi-poc \
  --query 'KeyMaterial' \
  --output text > key-pair-poridhi-poc.pem
chmod 400 key-pair-poridhi-poc.pem

# Login to Pulumi and use access key (saved it initially)
pulumi login

# Select existing stack
pulumi stack select zim10/data-drift-monitoring/dev

# Refresh state — clears old AWS resources (critical for Poridhi!)
pulumi refresh --yes

# Deploy fresh infrastructure
pulumi up --yes
```

> ✅ Note down the **EC2 Public IP** and **S3 Bucket Name** from the output!


### Phase 3 — Upload ML Model to S3

# After pulumi up — get your real bucket name
pulumi stack output models_bucket_name

# Update s3_model_deploy.py with this bucket name
# Then run:
python3 s3_model_deploy.py

```bash
cd ..

# Download model
curl -o model.pkl https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Model/logistic_regression_model.pkl

# Create s3_model_deploy.py with your bucket name and run:
python3 s3_model_deploy.py

# ⚠️ Never push s3_model_deploy.py to GitHub!
```

### Phase 4 — Set Up IAM Permissions

- Go to **AWS Console → IAM → Policies → Create Policy**
- Create policy `S3ModelAccessPolicy` with S3 access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
            "Resource": [
                "arn:aws:s3:::YOUR_S3_BUCKET_NAME",
                "arn:aws:s3:::YOUR_S3_BUCKET_NAME/*"
            ]
        }
    ]
}
```

- Create role `EC2S3AccessRole` and attach `S3ModelAccessPolicy`
- Attach the role to your EC2 instance via **Actions → Security → Modify IAM Role**





### Phase 5 — Build and Push Docker Image
- if you have updated docker image in your Docker Repositores, you can skip phase-5 but during deploy this image in EC2 instance, must Update docker-compose.yml section in EC2 instance, open docker-compose.yml using nano and update bucket name here. then you do not need to push your image to docker hub, can skip the following line. 

```bash
cd fastapi-app

# Update S3_BUCKET in main.py with your bucket name
docker build -t churn-prediction-app .
docker tag churn-prediction-app:latest <your-dockerhub-username>/churn-prediction-app:latest
docker push <your-dockerhub-username>/churn-prediction-app:latest
```

### Phase 6 — Deploy on EC2

```bash
# SSH into EC2
ssh -i infrastructure/key-pair-poridhi-poc.pem ubuntu@<EC2-PUBLIC-IP>

# Install Docker on EC2
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo chmod 666 /var/run/docker.sock
sudo usermod -aG docker ${USER}
newgrp docker

# ⚠️ Reboot EC2 if Docker fails to start (kernel mismatch issue)
sudo reboot
# SSH back in after 1-2 minutes

# Clone repo and run containers
git clone https://github.com/zim10/data-drift-monitoring.git
cd data-drift-monitoring
docker-compose up -d

# Verify all 4 containers running
docker ps
```

### Phase 7 — Run Drift Simulator

```bash
# On Poridhi server (not EC2)
cd ~/data-drift-monitoring/drift-simulation

# Download dataset
curl -o WA_FnUseC_TelcoCustomerChurn.csv \
  https://raw.githubusercontent.com/minhaz00/MLOps-Project-Customer-Churn-Prediction/main/Data/Telco-Customer-Churn.csv

# Update EC2 IP in drift_simulator.py first then run:
python3 drift_simulator.py
```

### Phase 8 — Visualize in Grafana

1. Open `http://<EC2-PUBLIC-IP>:3000` → Login: `admin/admin`
2. Go to **Settings → Data Sources → Add Prometheus**
3. URL: `http://<EC2-PUBLIC-IP>:9090` → **Save & Test**
4. Go to **Dashboards → New Dashboard → Add Visualization**
5. Use these Prometheus queries:

| Panel | Prometheus Query |
|---|---|
| Feature Drift Score | `churn_feature_drift` |
| Total Predictions | `churn_prediction_count_total` |
| API Latency | `churn_prediction_latency_seconds` |
| Input Feature Values | `churn_input_feature` |
| Prediction Distribution | `churn_prediction_distribution` |

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

## Useful Docker Commands

```bash
docker-compose up -d       # start all containers
docker-compose down        # stop all containers
docker ps                  # check running containers
docker logs churn-api      # view API logs
docker logs prometheus     # view Prometheus logs
docker logs grafana        # view Grafana logs
docker logs postgres       # view DB logs
docker restart churn-api   # restart a container
```

---

## Key Pulumi Commands

```bash
pulumi login                                          # login to Pulumi cloud
pulumi stack select zim10/data-drift-monitoring/dev   # select stack
pulumi stack                                          # check stack and resources
pulumi preview                                        # preview what will be created
pulumi up --yes                                       # deploy infrastructure
pulumi refresh --yes                                  # sync state with real AWS
pulumi destroy --yes                                  # destroy all resources
```

---

## Important Notes

- Never push `.pem` files, `.env`, `model.pkl`, or `*.csv` to GitHub
- `s3_model_deploy.py` contains your bucket name — never push it
- Always run `git status` before pushing
- Use feature branches for new features: `git checkout -b feature/name`
- Pulumi creates its own `.venv` inside `infrastructure/` — this is normal!

---

## Roadmap

- [x] Phase 1 — Basic drift monitoring (FastAPI + Prometheus + Grafana)
- [ ] Phase 2 — Model drift detection
- [ ] Phase 3 — Automated alerting in Grafana
- [ ] Phase 4 — Automated retraining trigger
- [ ] Phase 5 — CI/CD pipeline

---

## Conclusion

This system provides a robust framework for maintaining ML model reliability in production. By leveraging Prometheus for metrics collection and Grafana for visualization, it enables proactive model maintenance rather than reactive fixes after business impact has occurred.

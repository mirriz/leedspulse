# RailPulse API

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Render](https://img.shields.io/badge/Deployment-Render-46E3B7?style=flat&logo=render&logoColor=white)

**RailPulse** is a transport analytics engine that fuses **telemetry** (National Rail live data) with **crowd sentiment** (passenger reports) to determine the stress level of UK rail hubs.

### **[View Live Deployment](https://railpulse-w5g2.onrender.com)**
### **[View Live API Documentation](https://railpulse-w5g2.onrender.com/docs)**

---

## Project Rationale

Traditional transport apps only show delays. They fail to capture the passenger experience.

RailPulse solves this via **Novel Data Integration**:
1.  **Ingests Live Data:** Consumes the Huxley National Rail proxy for real-time arrivals/departures.
2.  **Crowdsources Incidents:** Allows authenticated users to report specific issues (crowding, antisocial behaviour).
3.  **The Hub Health Algorithm:** Merges these inputs into a normalised Stress Index (0.0 - 1.0) to visualise station health instantly.

---

## Features

### Advanced Security & Auth
* **JWT Authentication:** Stateless, secure, and scalable Bearer token architecture.
* **RBAC (Role-Based Access Control):** Users strictly own their data; incidents can only be modified/deleted by their creator.
* **Password Hashing:** Uses `bcrypt` for industry-standard credential protection.

### Intelligent Analytics (Stress Index)
The core IP of this project is the weighted algorithm found in `src/routers/analytics.py`. It determines station status based on:
* **60% Weight:** Live Rail Delay (Normalised to 60 mins).
* **40% Weight:** User Report Severity (Last 1 hour).
* **Override:** If `cancelled_trains > threshold`, the status forces **RED** regardless of delay metrics.

### Cloud-Native Architecture
* **API Hosting:** Render (Containerised Python Environment).
* **Database:** Azure Database for PostgreSQL (Enterprise-grade storage).
* **Connectivity:** Securely bridged via whitelisted firewall rules to allow serverless communication.

---

## Technology Stack

| Component | Technology | Justification |
| :--- | :--- | :--- |
| **Framework** | **FastAPI** | Chosen for asynchronous performance and OpenAPI (Swagger) generation. |
| **Database** | **PostgreSQL** | Relational integrity required for User-Incident relationships. Hosted on Azure. |
| **ORM** | **SQLAlchemy** | Provides SQL injection protection and Pythonic database abstraction. |
| **External API** | **Huxley 2** | A JSON proxy for the SOAP-based National Rail Darwin Data Feeds. |
| **Testing** | **Pytest** | Industry standard testing framework for unit and integration tests. |

---

## Local Setup Instructions

Follow these steps to run the API locally for development or marking.

### 1. Clone & Configure
```bash
git clone [https://github.com/mirriz/railpulse.git](https://github.com/mirriz/railpulse.git)
cd railpulse
```

### 2. Virtual Environment
```bash
# Create virtual environment (Python 3.11.8)
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
**DATABASE_URL**=postgresql://user:password@localhost/railpulse_db
**SECRET_KEY**=your_secret_key_here
**OLDBWS_TOKEN**=your_huxley_token_here

### 5. Run the Server
```bash
uvicorn src.main:app --reload
```

## Testing
The project includes a test suite covering Authentication, CRUD operations, and the Analytics Algorithm.

To run tests:

```bash
pytest -v
```

## Project Structure

```text
railpulse/
├── src/
│   ├── routers/
│   │   ├── analytics.py   # Algorithm & Live Data
│   │   ├── auth.py        # User Registration & Login 
│   │   └── incidents.py   # CRUD Operations for Reports
│   ├── sql/
│   │   ├── create_tables.sql  # Schema definition
│   │   └── drop_tests.sql     # Script for testing
│   ├── auth.py            # JWT Logic, Password Hashing & RBAC
│   ├── database.py        # Database Connection
│   ├── main.py            # Application Entrypoint
│   ├── models.py          # SQLAlchemy Database Models
│   ├── rail_service.py    # National Rail (Huxley) API Integration
│   └── schemas.py         # Pydantic Data Validation
├── tests/
│   └── test_main.py       # Test Suite
├── pytest.ini             # Test Configuration
├── requirements.txt       # Dependencies
└── README.md              # Documentation
```

## Academic Integrity 
This project is submitted for COMP3011: Web Services and Web Data.

Author: Alexander East

Declaration: GenAI was used for planning, debugging, and structuring code and comments as per the assessment category.






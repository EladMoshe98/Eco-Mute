# EcoMute – Bike Rental REST API

A FastAPI-based async REST API for managing an urban e-bike rental system, built as a university graduate project.

---

## Features

- **Bikes** – full CRUD, status filter (`available` / `rented` / `maintenance`)
- **Users** – registration, lookup, deletion, Argon2 password hashing
- **Stations** – admin-managed docking stations
- **Rentals** – create / end rentals with business-rule enforcement (battery ≥ 20%, bike not already rented)
- **Auth** – JWT bearer tokens via OAuth2, role-based access control (`admin` / `user`)
- **ML Prediction** – scikit-learn linear regression model to estimate trip duration
- **Logging** – structured logger injected via FastAPI `Depends()`, console + file handlers
- **Streamlit frontend** – simple UI for interacting with the API
- **63 automated tests** – CRUD, auth flows, edge cases, input validation, rental lifecycle

---

## Project Structure

```
lab2/
├── app/
│   ├── main.py                      # FastAPI app + lifespan
│   ├── logger.py                    # Logging setup
│   ├── security.py                  # JWT + password hashing
│   ├── database_layer/              # SQLAlchemy models + DB engine
│   │   ├── database.py
│   │   └── models.py
│   ├── data_transfer_schemas/       # Pydantic request/response schemas
│   │   └── schemas.py
│   ├── routers/                     # API route handlers
│   │   ├── auth.py
│   │   ├── bikes.py
│   │   ├── users.py
│   │   ├── rentals.py
│   │   ├── stations.py
│   │   ├── admin_router.py
│   │   └── prediction.py
│   ├── services/                    # Business logic (pricing etc.)
│   └── ml/                          # Trained model + training script
├── frontend/
│   └── app.py                       # Streamlit UI
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_comprehensive.py
│   ├── test_edge_cases.py
│   ├── test_logic.py
│   └── test_schemas.py
├── .env                             # Secret keys (not committed)
├── .gitignore
└── requirements.txt
```

---

## Getting Started

### 1. Clone & create virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/ecomute-lab2.git
cd ecomute-lab2
python -m venv venv
```

### 2. Activate the virtual environment

```bash
# PowerShell
.\venv\Scripts\Activate.ps1

# Command Prompt
venv\Scripts\activate.bat

# Git Bash
source venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the project root:

```
SECRET_KEY=your_long_random_secret_here
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

API is available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 6. Run the Streamlit frontend (optional)

```bash
streamlit run frontend/app.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/token` | — | Login, returns JWT |
| GET | `/bikes/` | — | List all bikes |
| POST | `/bikes/` | — | Create a bike |
| PUT | `/bikes/{id}` | — | Update a bike |
| DELETE | `/bikes/{id}` | — | Delete a bike |
| GET | `/users/` | — | List all users |
| POST | `/users/` | — | Register a user |
| DELETE | `/users/{id}` | — | Delete a user |
| GET | `/stations/` | — | List all stations |
| POST | `/stations/` | Admin | Create a station |
| DELETE | `/stations/{id}` | Admin | Delete a station |
| POST | `/rentals/` | — | Start a rental |
| POST | `/rentals/{id}/end` | — | End a rental |
| POST | `/predict/` | — | Predict trip duration |

---

## Tech Stack

- **FastAPI** – async web framework
- **SQLAlchemy 2.0** – async ORM with aiosqlite
- **Pydantic v2** – data validation
- **python-jose** – JWT tokens
- **passlib + argon2** – password hashing
- **scikit-learn** – ML prediction model
- **Streamlit** – frontend
- **pytest + httpx** – testing

---

## License

MIT
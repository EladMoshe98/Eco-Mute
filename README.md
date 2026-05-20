# EcoMute – Urban E-Bike Rental API

A FastAPI-based async REST API for managing an urban e-bike rental system, built as a graduate project at IE Business School.

## Quickstart

```bash
git clone https://github.com/eladmoshe98/Eco-Mute.git
cd Eco-Mute
pip install -r requirements.txt
cp .env.example .env   # add your secret key
uvicorn app.main:app --reload
```

Streamlit frontend:
```bash
streamlit run frontend/app.py
```

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

## Project Structure

```
lab2/
├── app/
│   ├── main.py
│   ├── security.py
│   ├── database_layer/
│   ├── data_transfer_schemas/
│   ├── routers/
│   ├── services/
│   └── ml/
├── frontend/
│   └── app.py
└── tests/
```

## Tech Stack

Python · FastAPI · SQLAlchemy · Pydantic · JWT · Argon2 · scikit-learn · Streamlit · pytest

# 🔐 Auth Service (FastAPI + PostgreSQL + JWT)

A production-ready authentication service built with:

-   FastAPI
-   PostgreSQL (Docker)
-   JWT Access Tokens
-   Refresh Token Rotation
-   Reuse Detection (Security Option A)
-   Logout & Logout-All
-   Rate Limiting (SlowAPI)
-   Swagger Documentation with Bearer Auth
-   Global Error Handling
-   Security Headers Middleware
-   Pytest Test Suite

------------------------------------------------------------------------

## 🚀 Features

### Authentication Flow

-   Access Token (JWT)
-   Refresh Token (stored hashed in DB)
-   Token Rotation
-   Reuse Detection (revokes all sessions if replay attack detected)

### Security

-   Password hashing (bcrypt)
-   Refresh token hashing (SHA-256)
-   Rate limiting per IP
-   Security headers
-   Standardized error responses

### Developer Experience

-   Swagger UI with Authorize button
-   JSON login endpoint for easy testing
-   Dockerized Postgres
-   PowerShell dev scripts
-   Automated tests (pytest)

------------------------------------------------------------------------

# Requirements

-   Python 3.12+
-   Docker Desktop
-   Windows PowerShell (recommended)

------------------------------------------------------------------------

# Setup (Windows PowerShell)

## Enter project directory

``` powershell
cd C:\Users\YourUser\Desktop\auth_service
```

## Create virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Install dependencies

``` powershell
pip install -r requirements.txt
```

If no requirements file exists:

``` powershell
pip install fastapi "uvicorn[standard]" sqlmodel "psycopg[binary]" PyJWT passlib[bcrypt] slowapi python-dotenv pytest httpx
```

------------------------------------------------------------------------

# Database (PostgreSQL via Docker)

## Start database

``` powershell
docker compose up -d
```

## Reset database (WARNING: deletes data)

``` powershell
docker compose down -v
docker compose up -d
```

------------------------------------------------------------------------

# Running the API

``` powershell
python -m uvicorn app.main:app --reload
```

Swagger available at:

http://127.0.0.1:8000/docs

------------------------------------------------------------------------

# Recommended Test Flow (Swagger)

1.  POST /auth/register
2.  POST /auth/login-json
3.  Click Authorize and paste access token
4.  GET /auth/me
5.  POST /auth/refresh
6.  Try using old refresh again (reuse detection test)
7.  POST /auth/logout-all

------------------------------------------------------------------------

# Run Tests

``` powershell
python -m pytest -q
```

------------------------------------------------------------------------

# Security Notes

-   Refresh tokens are stored hashed.
-   Reuse detection revokes all sessions upon replay attack.
-   Access tokens are short-lived.
-   Rate limiting protects authentication endpoints.
-   Security headers enabled.

------------------------------------------------------------------------

# Autor
**Eduardo Dalla Porta**

------------------------------------------------------------------------

#  Contato

- LinkedIn: [/in/eduardo-dalla-porta](https://www.linkedin.com/feed/)
- GitHub: [eduardodallaporta](https://github.com/eduardodallaporta)

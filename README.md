# E-Ombor Platform

## Stage 1: Authentication and Platform Foundation

This repository contains the first stage of the E-Ombor platform:
- Django REST API backend (`backend/`)
- React frontend (`frontend/`)
- Password-based registration and login only
- No e-imzo or 1C integration in this stage

## Next stages
1. Add dashboard and role-based UI flows
2. Add warehouse / procurement modules
3. Add object/project tracking and analytics
4. Add e-signature and 1C integration later

## Getting started

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API endpoints (stage 1)
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/auth/user/`
- `GET /api/api/dashboard/`

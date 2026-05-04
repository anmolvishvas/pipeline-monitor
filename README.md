# Pipeline Monitor

A full-stack pipeline monitoring system built with Django (DRF) and Vue 3.  
It allows users to trigger jobs, monitor stage execution, and view live logs with real-time updates.

---

## 🚀 Features

- List all jobs with live status badges
- Expand a job to view stage timeline (no navigation)
- Live log streaming (polling-based)
- Optimistic UI updates on trigger/retry
- Error handling with inline alerts and visual feedback
- Role-based UI (Operator vs Viewer)
- Global filtering (status + error) without refetching

---

## 🏗️ Tech Stack

**Backend**
- Django
- Django REST Framework
- SQLite

**Frontend**
- Vue 3 (Composition API)
- Axios

---

## ⚙️ Setup Instructions

### 1. Clone repository

```bash
git clone https://github.com/anmolvishvas/pipeline-monitor
cd pipeline-monitor
```
### 2. Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs on:
```bash
http://127.0.0.1:8000
```
### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Backend runs on:
```bash
http://127.0.0.1:5173
```
### 🔐 Demo Users

Operator:
username: operator@test.com
password: test1234

Viewer:
username: viewer@test.com
password: test1234

### 🧪 Seed Demo Data

Run:
```bash
python manage.py shell
```
Then:
```bash
exec(open("seed.py").read())
```
This creates:
5 jobs
3 stages each
mixed states (queued, running, completed, failed)

## 🖥️ How It Works

### Job Flow
queued → running → completed
running → failed → retry


### Stage Flow

pending → running → done
running → failed

---

## 🔁 Polling Strategy

- Job list: refreshed every 5 seconds  
- Stage logs: only one active poller at a time  
- Polling stops automatically when stage completes  

---

## ⚡ Key Design Decisions

See `DECISIONS.md` for details on:

- N+1 query optimization using `prefetch_related`  
- Single active poller implementation  
- Polling vs WebSocket tradeoff  

---

## 🧩 API Overview

| Endpoint | Description |
|--------|------------|
| GET /api/jobs/ | List jobs |
| POST /api/jobs/:id/trigger/ | Trigger/retry job |
| GET /api/jobs/:id/stages/ | Get stages + logs |
| POST /api/stages/:id/logs/ | Create log |
| GET /api/me/ | Get current user role |

---

## 🎯 Demo Flow

1. Open dashboard  
2. Trigger a queued job  
3. Expand stages  
4. Watch logs update live  
5. Observe failure + retry  
6. Use filters  

---

## 📌 Notes

- Filtering is client-side (no extra API calls)  
- UI updates optimistically for better UX  
- Backend enforces permissions (frontend is display-only gating)  

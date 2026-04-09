# LawLink (LawChatbot)

LawLink is a multi-component legal assistant platform focused on Indian law.  
It combines:

- a React frontend for users and lawyers,
- a Node.js backend for authentication and service workflows,
- a Python FastAPI backend for legal-document retrieval and AI-assisted answers,
- and a legal dataset used for search and response grounding.

## Project Structure

```text
lawchatbot/
├── law-backend-main/      # Node.js + Express backend (auth, users, lawyers, appointments)
├── law-frontend-main/     # React + Vite frontend (dashboard, chat, auth, lawyer UI)
├── backend/               # Python + FastAPI backend (AI/ML legal search + chat API)
├── dataset/               # Legal documents, processed data, vectors, and models
└── README.md
```

## Components

### 1) `law-frontend-main`

Frontend application built with React and Vite.

Main responsibilities:
- User and lawyer authentication pages
- User dashboard and lawyer dashboard
- Chatbot interfaces
- Appointment and profile views

Typical run command:

```bash
cd law-frontend-main
npm install
npm run dev
```

Default local URL: `https://law.skyzin.com`

---

### 2) `law-backend-main`

Backend application built with Node.js, Express, and MongoDB.

Main responsibilities:
- Authentication and authorization (JWT)
- User and lawyer management
- Appointment APIs
- General chat/business routes

Typical run command:

```bash
cd law-backend-main
npm install
npm start
```

Expected local API base: `https://law-api.skyzin.com/api`

---

### 3) `backend`

AI/ML backend built with Python and FastAPI.

Main responsibilities:
- Legal document ingestion and processing
- Search over legal content (including vector/semantic retrieval)
- Chat endpoint for legal Q&A
- Health/stat endpoints for monitoring

Typical run command:

```bash
cd backend
pip install -r requirements.txt
python run_system.py --action setup
python src/api/main.py
```

Expected local API base: `https://llm.skyzin.com/api`

---

### 4) `dataset`

Legal knowledge base and related artifacts.

Contains:
- Source legal documents
- Processed/training-ready text
- Vector database/index files
- Model and metadata assets

This folder powers legal grounding for the AI backend.

## How LawLink Works (High Level)

1. User interacts with the React frontend (`law-frontend-main`).
2. Frontend calls backend APIs:
   - Node backend (`law-backend-main`) for auth, profile, lawyer, and appointment flows.
   - Python backend (`backend`) for legal Q&A and document retrieval.
3. Python backend uses `dataset` for relevant legal context.
4. Response is returned to the user interface.

## Prerequisites

- Node.js (LTS recommended)
- Python 3.10+
- MongoDB
- Environment variables for API keys and database URLs

## Quick Start (All Services)

Open separate terminals and run:

### Terminal 1 - Python AI Backend
```bash
cd backend
pip install -r requirements.txt
python run_system.py --action setup
python src/api/main.py
```

### Terminal 2 - Node Backend
```bash
cd law-backend-main
npm install
npm start
```

### Terminal 3 - Frontend
```bash
cd law-frontend-main
npm install
npm run dev
```

## Notes

- Folder name requested as `/law-fronted-main` appears to be `law-frontend-main` in this project.
- Keep all required `.env` values configured in backend folders before production use.


# LLM Guardrails Microservices Prototype
[![CI](https://github.com/rahul-pawan-somani/llm-guardrails-microservices/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/rahul-pawan-somani/llm-guardrails-microservices/actions/workflows/ci.yml)

## Overview

This project implements a three-service microservices architecture for Large Language Model (LLM) safety and content moderation.

The system consists of three independent services that work together to process user prompts, apply configurable guardrails, interact with a language model, and sanitise generated responses before they are returned to users.

Guardrails are centrally managed through a Firebase Realtime Database and are automatically applied to both incoming prompts and outgoing model responses.

---

## Technologies Used

* Python
* Flask
* REST APIs
* Firebase Realtime Database
* Mistral API
* Requests
* Docker
* Docker Compose
* GitHub Actions
* Microservices Architecture

---

## System Architecture

```text
                    User Request
                          │
                          ▼
                ┌─────────────────┐
                │     Auberge     │
                │  Orchestrator   │
                └────────┬────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│   Guardrails    │              │       LLM       │
│    Service      │              │    Service      │
└────────┬────────┘              └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Firebase RTDB   │
│ Guardrail Store │
└─────────────────┘
```

---

## Microservices

### 1. LLM Service

The LLM service acts as a lightweight wrapper around the Mistral API.

Responsibilities:

* Accept user prompts
* Forward requests to Mistral
* Return generated responses
* Handle API and validation errors
* Provide a simple REST interface for language model access

Endpoint:

```http
POST /llm
```

Request:

```json
{
  "prompt": "What is the capital of Italy?"
}
```

Response:

```json
{
  "output": "Rome is the capital of Italy."
}
```

---

### 2. Guardrails Service

The Guardrails service manages all content filtering rules.

Each guardrail consists of:

* Unique identifier
* Regular expression pattern
* Replacement string

Guardrails are stored centrally using Firebase Realtime Database.

Supported operations:

* Create guardrails
* Read guardrails
* Delete guardrails
* List all guardrails

Example guardrail:

```json
{
  "id": "email-001",
  "regx": "[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+",
  "sub": "<Email Address>"
}
```

Supported endpoints:

```http
PUT    /guardrails/{id}
GET    /guardrails/{id}
DELETE /guardrails/{id}
GET    /guardrails
```

---

### 3. Auberge Service

The Auberge service acts as the orchestration layer.

Responsibilities:

* Receive user prompts
* Retrieve active guardrails
* Apply input sanitisation
* Forward sanitised prompts to the LLM service
* Apply output sanitisation
* Return the protected response

This service ensures that both inputs and outputs pass through the same safety pipeline.

Endpoint:

```http
POST /auberge
```

---

## Guardrail Processing Workflow

```text
User Prompt
     │
     ▼
Input Guardrails
     │
     ▼
 Sanitised Prompt
     │
     ▼
   LLM Service
     │
     ▼
 Raw Response
     │
     ▼
Output Guardrails
     │
     ▼
 Sanitised Response
     │
     ▼
     User
```

---

## Example Workflow

### Active Guardrails

```json
[
  {
    "id": "roma",
    "regx": "Rome",
    "sub": "Roma"
  },
  {
    "id": "firenze",
    "regx": "Florence",
    "sub": "Firenze"
  }
]
```

### User Prompt

```json
{
  "prompt": "What are the major cities of Italy?"
}
```

### Example Output

```json
{
  "output": "Roma, Milano, Napoli and Firenze are among the major cities of Italy."
}
```

Configured guardrails automatically modify generated content before it reaches the user.

---

## Repository Structure

```text
llm-guardrails-microservices/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── tests/
│   ├── __init__.py
│   ├── firebase_helper.py
│   ├── test_integration_live.py
│   └── test_services.py
│
├── .dockerignore
├── .env.example
├── .gitignore
│
├── Dockerfile
├── compose.yml
│
├── auberge.py
├── guardrails.py
├── llm.py
│
├── requirements.txt
└── README.md
```

---

## Getting Started

### Install Dependencies

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

### Environment Configuration

Create a local environment file from the supplied template:

```bash
cp .env.example .env
```

Update `.env` with the required Firebase and Mistral credentials:

```env
FIREBASE_DB=your-firebase-project-id
MISTRAL_API_KEY=your-mistral-api-key
```

For a default Firebase Realtime Database in `europe-west1`, `FIREBASE_DB` is the portion of the database name before `-default-rtdb`.

For example, for:

```text
https://guardrails-3d1c1-default-rtdb.europe-west1.firebasedatabase.app](https://example-project-default-rtdb.europe-west1.firebasedatabase.app
```

use:

```env
FIREBASE_DB=example-project
```

The `.env` file contains local credentials and is excluded from version control through `.gitignore`.

### Run with Docker Compose

With Docker running:

```bash
docker compose up --build
```

The services are exposed on:

| Service    | Port |
| ---------- | ---: |
| LLM        | 3000 |
| Guardrails | 3001 |
| Auberge    | 3002 |

Health endpoints are available at:

```text
http://localhost:3000/health
http://localhost:3001/health
http://localhost:3002/health
```

### Local Development

To run the services directly without Docker, first load the environment variables:

```bash
set -a
source .env
set +a
```

Then run each service in a separate terminal:

```bash
python llm.py
```

```bash
python guardrails.py
```

```bash
python auberge.py
```

---

## Testing

### Automated Service Tests

The deterministic test suite uses mocked external Firebase and Mistral requests so that service behaviour can be tested reliably without external credentials.

Run locally with:

```bash
python -m unittest tests.test_services -v
```

The automated suite covers:

* request validation;
* Mistral response handling;
* regular-expression validation;
* Firebase CRUD behaviour through mocked HTTP responses;
* input and output sanitisation;
* downstream-service failure handling.

The same deterministic suite runs through GitHub Actions on pushes to `main` and on pull requests.

### Live Integration Tests

A separate five-test integration suite exercises the running microservices against configured Firebase and Mistral dependencies.

First load the local environment configuration:

```bash
set -a
source .env
set +a
```

With all three services running, execute:

```bash
RUN_LIVE_TESTS=1 python -m unittest tests.test_integration_live -v
```

The live integration suite covers:

* LLM service communication;
* Firebase-backed guardrail creation and retrieval;
* invalid regular-expression rejection;
* service-to-service orchestration;
* end-to-end output sanitisation.

> Temporary guardrails created by the live integration tests are removed individually after each test.

---

## Key Features

- Three-service Flask microservices architecture
- Mistral LLM integration
- Firebase-backed guardrail storage
- Regex-based configurable content filtering
- Input and output sanitisation
- REST-based service communication
- Environment-based service configuration
- Docker Compose orchestration
- Structured service logging
- Deterministic CI testing
- Five-test live integration suite


---

## Future Improvements

Potential future enhancements include:

- authentication and authorisation;
- role-based guardrail administration;
- guardrail prioritisation and ordering;
- user-specific guardrail profiles;
- semantic guardrails using embedding models;
- centralised log aggregation and distributed tracing;
- Kubernetes deployment;
- real-time guardrail analytics and monitoring.

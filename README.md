# LLM Guardrails Microservices System

## Overview

This project implements a distributed microservice architecture for Large Language Model (LLM) safety and content moderation.

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
* Microservices Architecture
* Distributed Systems

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
  "regx": "[a-zA-Z0-9_.]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+",
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

The output demonstrates how configured guardrails automatically modify generated content before it reaches the user.

---

## Integration Testing

The repository includes automated integration tests that verify communication between all three services.

The tests validate:

* LLM endpoint functionality
* Guardrail CRUD operations
* Regular expression validation
* Firebase persistence
* Service orchestration
* End-to-end guardrail application

Example scenarios include:

* Replacing sensitive information using regular expressions
* Rejecting invalid guardrail definitions
* Verifying sanitisation of LLM outputs
* Confirming distributed service communication

---

## Repository Structure

```text
.
├── auberge.py
├── guardrails.py
├── llm.py
├── database.py
├── test5.py
├── requirements.txt
└── README.md
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Environment Variables

The system requires the following environment variables:

### Firebase

```text
FIREBASE_DB=<firebase_database_name>
```

Example:

```text
FIREBASE_DB=guardrails-3d1c1
```

### Mistral

```text
MISTRAL_API_KEY=<your_api_key>
```

---

## Running the Services

### Terminal 1

```bash
python llm.py
```

Runs on:

```text
localhost:3000
```

---

### Terminal 2

```bash
python guardrails.py
```

Runs on:

```text
localhost:3001
```

---

### Terminal 3

```bash
python auberge.py
```

Runs on:

```text
localhost:3002
```

---

## Running Tests

```bash
python test5.py
```

The test suite validates end-to-end functionality across all microservices.

---

## Key Features

* Distributed microservice architecture
* LLM integration using Mistral
* Firebase-backed guardrail storage
* Regex-based content filtering
* Input sanitisation
* Output sanitisation
* REST API communication
* Automated integration testing
* Centralised guardrail management

---

## Skills Demonstrated

* Software Engineering
* Distributed Systems
* Microservices Architecture
* REST API Development
* Flask
* Firebase
* Generative AI Integration
* AI Safety
* Content Moderation
* Automated Testing
* Python Development

---

## Future Improvements

Potential future enhancements include:

* Role-based guardrail administration
* Guardrail prioritisation and ordering
* User-specific guardrail profiles
* Audit logging and monitoring
* Docker containerisation
* Kubernetes deployment
* Authentication and authorisation
* Semantic guardrails using embedding models
* Real-time analytics dashboard

```
```

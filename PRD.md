# Product Requirements Document
# Real-Time Fake News Detection Platform
### Powered by Flask & Machine Learning

| Field | Details |
|-------|---------|
| **Document Version** | 1.0 |
| **Status** | Draft — For Review |
| **Author** | Product Team |
| **Date** | April 2026 |
| **Tech Stack** | Python · Flask · NLP · REST API |
| **Reviewer** | Engineering & Stakeholders |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Objectives](#3-goals--objectives)
4. [Scope](#4-scope)
5. [User Personas](#5-user-personas)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [System Architecture](#8-system-architecture)
9. [ML & NLP Pipeline](#9-ml--nlp-pipeline)
10. [Security Requirements](#10-security-requirements)
11. [User Stories](#11-user-stories)
12. [Release Plan](#12-release-plan)
13. [Success Metrics & KPIs](#13-success-metrics--kpis)
14. [Dependencies & Risks](#14-dependencies--risks)
15. [Assumptions](#15-assumptions)
16. [Glossary](#16-glossary)

---

## 1. Executive Summary

Misinformation and fake news represent one of the most critical challenges of the digital information age. The **Real-Time Fake News Detection Platform** is a web-based application built on **Flask** that leverages Natural Language Processing (NLP) and Machine Learning (ML) to automatically identify and flag potentially false or misleading news articles.

The system provides journalists, researchers, social media platforms, and everyday users with an instant credibility score for any piece of submitted content — reducing the time-to-flag from hours to milliseconds.

This document defines the scope, goals, features, technical requirements, and success criteria for **Version 1.0** of the platform.

---

## 2. Problem Statement

### 2.1 Background

The rapid proliferation of online news and social media has made it increasingly difficult to distinguish authentic journalism from intentional disinformation. Key challenges include:

- Over **60% of adults globally** encounter misinformation regularly *(Reuters Institute, 2025)*.
- Manual fact-checking is slow, expensive, and does not scale with the volume of content published daily.
- Existing browser-based tools are **reactive** — they flag content after it has already spread.
- There is no unified, API-first solution enabling developers to integrate real-time detection into their own platforms.

### 2.2 Opportunity

An automated, API-accessible detection engine can reduce the time to flag suspicious content from hours to milliseconds. By building on Flask, the platform benefits from a lightweight, extensible Python ecosystem with native integration to ML libraries (`scikit-learn`, `transformers`, `spaCy`).

---

## 3. Goals & Objectives

### 3.1 Product Goals

- Deliver **real-time credibility scoring** for news articles and text snippets.
- Expose a well-documented **REST API** so third-party developers can integrate detection capabilities.
- Provide an intuitive **web interface** for non-technical end-users.
- Maintain model accuracy above **92% F1-score** on the benchmark dataset.

### 3.2 Business Objectives

- Launch public beta within **12 weeks** of project kickoff.
- Onboard **10 pilot partners** (newsrooms, social platforms, or browser extension developers).
- Achieve **< 500 ms** average API response time under standard load.

---

## 4. Scope

### 4.1 In Scope

- Flask web application with UI for article/text submission.
- REST API endpoints for programmatic access.
- NLP preprocessing pipeline (tokenisation, stop-word removal, lemmatisation).
- ML classification model (baseline: Logistic Regression; advanced: BERT fine-tuning).
- Credibility score + category label: `Real` / `Likely Real` / `Uncertain` / `Likely Fake` / `Fake`.
- Confidence interval and contributing feature explanations (Explainable AI).
- User dashboard with submission history and analytics.
- Admin panel for model retraining and dataset management.
- HTTPS-secured deployment on a cloud provider (AWS / GCP / Railway).

### 4.2 Out of Scope (v1.0)

| Feature | Planned Version |
|---------|----------------|
| Browser extension | v1.2 |
| Real-time social media stream integration | v2.0 |
| Multi-language support (beyond English) | v1.5 |
| Mobile native applications | TBD |

---

## 5. User Personas

| Persona | Role | Primary Need | Pain Point |
|---------|------|-------------|-----------|
| **Ava — Journalist** | Staff reporter at online newspaper | Quickly verify sources before publishing | Manual checks take 2–4 hours per article |
| **Ben — Developer** | Backend engineer at social platform | API to flag posts at ingestion time | No reliable, low-latency detection API exists |
| **Carla — Researcher** | Academic studying misinformation | Bulk analysis of article datasets | Existing tools lack batch processing |
| **Dan — General User** | News reader on web browser | Instant trust score while reading | Cannot easily identify reliable sources |
| **Emma — Editor** | News desk editor | Dashboard for team submission history | No audit trail for fact-check decisions |

---

## 6. Functional Requirements

### 6.1 Web Interface

#### 6.1.1 Article Submission

- Users can paste **plain text**, a **URL**, or upload a `.txt` / `.pdf` file.
- Submission form validates that input length is between **50 and 10,000 characters**.
- Results are displayed within **3 seconds** of submission.

#### 6.1.2 Results Page

- Credibility score displayed as a **percentage (0–100%)** and a colour-coded label.
- Gauge chart illustrating overall score.
- Top 5 features driving the prediction (Explainable AI panel).
- Option to copy a shareable link or **export a PDF report**.

#### 6.1.3 User Dashboard

- Registered users can view history of all previous submissions.
- Filter and sort by date, score, and label.
- Aggregate statistics: average credibility score, total checks, label distribution chart.

---

### 6.2 REST API

#### 6.2.1 Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `POST` | `/api/v1/detect` | Submit text for real-time detection | API Key |
| `POST` | `/api/v1/detect/batch` | Submit up to 50 items in one request | API Key |
| `GET` | `/api/v1/result/{id}` | Retrieve stored result by ID | API Key |
| `GET` | `/api/v1/history` | List recent submissions for the API key | API Key |
| `GET` | `/api/v1/health` | Service health and model status | None |
| `POST` | `/api/v1/auth/token` | Obtain JWT token via credentials | None |

#### 6.2.2 Request / Response Contract — `POST /api/v1/detect`

**Request Body (JSON):**

```json
{
  "text": "string (50–10,000 chars) — mutually exclusive with url",
  "url": "string — public article URL, mutually exclusive with text",
  "return_features": "boolean (default: false)",
  "language": "string — ISO 639-1 code, only 'en' supported in v1.0"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes* | Article body or snippet (50–10,000 chars) |
| `url` | string | Yes* | Public URL of article (mutually exclusive with `text`) |
| `return_features` | boolean | No | Include feature importance in response (default: `false`) |
| `language` | string | No | ISO 639-1 code — only `en` supported in v1.0 |

**Response Body (JSON):**

```json
{
  "result_id": "uuid-string",
  "score": 0.82,
  "label": "LIKELY_REAL",
  "confidence": 0.91,
  "features": [...],
  "processing_ms": 214,
  "timestamp": "2026-04-19T08:30:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `result_id` | string | UUID for later retrieval |
| `score` | float | Credibility score 0.00–1.00 (higher = more credible) |
| `label` | string | `REAL` \| `LIKELY_REAL` \| `UNCERTAIN` \| `LIKELY_FAKE` \| `FAKE` |
| `confidence` | float | Model confidence in the label (0.00–1.00) |
| `features` | array | Top contributing features (if `return_features=true`) |
| `processing_ms` | integer | Server-side processing time in milliseconds |
| `timestamp` | string | ISO 8601 UTC timestamp |

---

### 6.3 Admin Panel

- Model performance dashboard (precision, recall, F1, confusion matrix).
- Upload new labelled datasets for incremental retraining.
- Trigger model retraining job with progress monitoring.
- Review flagged edge cases manually for labelling.
- API key management (create, revoke, set rate limits per key).

---

## 7. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | API response time (p95) | < 500 ms |
| **Performance** | Web UI result display | < 3 seconds |
| **Scalability** | Concurrent API requests | 500 req/s (horizontal scaling) |
| **Availability** | Service uptime SLA | 99.5% monthly |
| **Accuracy** | Classification F1-score | > 92% on benchmark dataset |
| **Security** | Data in transit | TLS 1.3 enforced |
| **Security** | API authentication | JWT + API key, rate-limited |
| **Privacy** | Submitted text retention | 30 days max, user-deletable |
| **Compliance** | GDPR readiness | Data deletion & export endpoints |
| **Maintainability** | Code coverage | > 80% unit + integration tests |

---

## 8. System Architecture

### 8.1 High-Level Components

| Layer | Technology | Responsibility |
|-------|-----------|---------------|
| **Presentation** | Flask · Jinja2 · Bootstrap 5 | Web UI rendering and form handling |
| **API Gateway** | Flask-RESTful · Flask-JWT-Extended | REST routing, auth, rate limiting |
| **NLP Pipeline** | spaCy · NLTK · regex | Tokenisation, cleaning, feature extraction |
| **ML Engine** | scikit-learn · HuggingFace Transformers | Model inference and explainability |
| **Task Queue** | Celery · Redis | Async batch processing and retraining jobs |
| **Database** | PostgreSQL · SQLAlchemy ORM | User data, submission history, model metadata |
| **Cache** | Redis | Response caching, rate limit counters, sessions |
| **Object Storage** | AWS S3 (or MinIO) | Datasets, model artefacts, PDF exports |
| **CI/CD** | GitHub Actions · Docker | Automated testing, containerised deployment |
| **Monitoring** | Prometheus · Grafana | Metrics, latency dashboards, alerting |

### 8.2 Flask Application Structure

```
project/
├── app/
│   ├── __init__.py          # Application factory: create_app()
│   ├── api/                 # Blueprints for REST API routes
│   │   ├── __init__.py
│   │   ├── detect.py        # /api/v1/detect, /api/v1/detect/batch
│   │   ├── results.py       # /api/v1/result/{id}, /api/v1/history
│   │   └── auth.py          # /api/v1/auth/token
│   ├── web/                 # Blueprints for web UI routes
│   │   ├── __init__.py
│   │   ├── views.py
│   │   └── dashboard.py
│   ├── models/              # SQLAlchemy database models
│   │   ├── user.py
│   │   ├── submission.py
│   │   └── api_key.py
│   ├── services/            # Business logic
│   │   ├── nlp_pipeline.py  # Preprocessing & feature extraction
│   │   ├── ml_engine.py     # Model loading & inference
│   │   └── result_store.py  # Persistence helpers
│   ├── tasks/               # Celery background tasks
│   │   ├── batch.py         # Batch detection processing
│   │   └── retrain.py       # Model retraining pipeline
│   └── utils/               # Shared helpers, validators, error handlers
├── config.py                # Environment-specific configuration
├── tests/                   # Pytest suites
│   ├── unit/
│   └── integration/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 8.3 Request Flow

```
User / Client
     │
     ▼
Nginx (reverse proxy + TLS termination)
     │
     ▼
Gunicorn (WSGI server — multiple workers)
     │
     ▼
Flask Application
     ├── Auth middleware (JWT / API Key validation)
     ├── Rate limiter (Flask-Limiter → Redis)
     │
     ▼
NLP Pipeline (spaCy · NLTK)
     │
     ▼
ML Engine (XGBoost / BERT)
     │
     ▼
Result stored in PostgreSQL + cached in Redis
     │
     ▼
JSON Response → Client
```

---

## 9. ML & NLP Pipeline

### 9.1 Preprocessing Steps

1. URL and HTML tag removal.
2. Unicode normalisation and lowercasing.
3. Tokenisation using spaCy English model (`en_core_web_sm` / `en_core_web_trf`).
4. Stop-word removal (NLTK stopwords corpus).
5. Lemmatisation.
6. Named Entity Recognition (NER) feature tagging.

### 9.2 Feature Engineering

| Feature | Method |
|---------|--------|
| TF-IDF vectors | Unigrams + bigrams, max 50k features |
| Sentiment polarity | VADER sentiment analyser |
| Readability score | Flesch-Kincaid grade level |
| Source credibility | Domain reputation lookup table |
| Entity density | Named entity count / total token count |
| Claim-to-evidence ratio | Heuristic pattern matching |

### 9.3 Model Architecture

| Model | Purpose | Latency | F1 Target |
|-------|---------|---------|-----------|
| Logistic Regression (TF-IDF) | Baseline fast classifier | < 50 ms | > 88% |
| Gradient Boosted Trees (XGBoost) | Ensemble classifier — **default** | < 100 ms | > 91% |
| Fine-tuned BERT (`bert-base-uncased`) | High-accuracy transformer — opt-in | < 400 ms | > 94% |

> **v1.0 default:** XGBoost for latency-sensitive requests. BERT available via `"model": "bert"` parameter.

### 9.4 Training Datasets

| Dataset | Size | Source |
|---------|------|--------|
| LIAR | 12,836 statements | politifact.com |
| FakeNewsNet (PolitiFact + GossipCop) | ~23,000 articles | GitHub |
| ISOT Fake News Dataset | 23,481 articles | University of Victoria |
| Pilot partner labels | Ongoing | Partner newsrooms |

---

## 10. Security Requirements

- All API endpoints require a valid **JWT token** or **API key** (`X-API-Key` header).
- Rate limiting: **60 requests/minute** per API key (configurable in admin panel).
- Input sanitisation and maximum length enforcement on all text fields.
- **OWASP Top 10** compliance — SQL injection prevention via ORM parameterised queries.
- **CSRF protection** on all web UI forms (Flask-WTF).
- Secrets managed via **environment variables** — never hardcoded.
- Regular dependency vulnerability scanning (GitHub Dependabot / `pip-audit`).
- Submitted text stored **encrypted at rest** (AES-256).

---

## 11. User Stories

| ID | As a… | I want to… | So that… | Priority |
|----|-------|-----------|---------|---------|
| US-01 | General user | Paste article text and see a credibility score | I can quickly assess reliability | **P0** |
| US-02 | General user | Submit a URL instead of copying text | I save time on content input | **P0** |
| US-03 | Developer | Call a REST API with article text | I can integrate detection in my app | **P0** |
| US-04 | Developer | Batch-submit up to 50 articles | I can process datasets efficiently | **P1** |
| US-05 | Journalist | See which features most influenced the score | I understand why content was flagged | **P1** |
| US-06 | Researcher | Download my submission history as CSV | I can analyse results externally | **P1** |
| US-07 | Editor | View a team dashboard with all submissions | I track my team's fact-check activity | **P2** |
| US-08 | Admin | Upload new training data and retrain the model | I can improve accuracy over time | **P1** |
| US-09 | Admin | Generate and revoke API keys | I control access to the service | **P0** |
| US-10 | General user | Export a shareable PDF credibility report | I can share evidence with others | **P2** |

---

## 12. Release Plan

| Milestone | Deliverable | Target |
|-----------|-------------|--------|
| **M0 — Kickoff** | Finalised PRD, team onboarding, repo setup | Week 1 |
| **M1 — Data & Model** | NLP pipeline, baseline model trained, > 88% F1 | Week 3 |
| **M2 — API Alpha** | Core Flask API endpoints functional, auth in place | Week 5 |
| **M3 — Web UI Beta** | Full web interface, dashboard, results page | Week 7 |
| **M4 — Integration** | Celery tasks, Redis caching, admin panel | Week 9 |
| **M5 — QA & Security** | Load testing, OWASP audit, bug fixes | Week 11 |
| **M6 — Public Beta** | Deployment to production, 10 pilot partners onboarded | Week 12 |
| **M7 — v1.0 GA** | Post-beta fixes, documentation, public launch | Week 16 |

---

## 13. Success Metrics & KPIs

| Metric | Definition | v1.0 Target |
|--------|-----------|------------|
| **Model F1-Score** | Weighted F1 on held-out test set | > 92% |
| **API Latency (p95)** | 95th-percentile API response time | < 500 ms |
| **Uptime** | Monthly service availability | > 99.5% |
| **API Adoption** | Active API keys used in 30-day window | > 10 partners |
| **User Submissions** | Total detections processed in first 30 days | > 5,000 |
| **User Satisfaction** | NPS survey from pilot users | > 40 |
| **False Positive Rate** | Real articles incorrectly flagged as Fake | < 5% |

---

## 14. Dependencies & Risks

### 14.1 External Dependencies

- HuggingFace model hub availability for BERT weights download.
- Public dataset licences (LIAR, FakeNewsNet) — redistribution terms must be confirmed.
- Cloud provider infrastructure (AWS / GCP) for deployment.
- Redis and PostgreSQL managed services.

### 14.2 Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| BERT inference too slow for SLA | Medium | High | Default to XGBoost; BERT as async opt-in |
| Training data bias / poor recall on new patterns | High | High | Monthly retraining cadence; human-in-the-loop review |
| Adversarial inputs crafted to evade detection | Medium | Medium | Ensemble approach; input diversity in training data |
| GDPR non-compliance for EU users | Low | High | Implement data deletion & export endpoints in v1.0 |
| Third-party dataset licence restrictions | Low | Medium | Legal review before training; maintain internal labelled set |
| Flask scalability under high load | Medium | High | Deploy behind Gunicorn + Nginx; horizontal auto-scaling |

---

## 15. Assumptions

- The initial model will be trained in **English only**; multi-language support requires separate NLP models.
- URL-based submission requires that the target URL is **publicly accessible** (no paywalls).
- Users are responsible for ensuring they have the right to submit content for analysis.
- The system is **not a legal fact-checking authority** — scores are probabilistic guidance only.
- Pilot partners will provide feedback and labelled examples for model improvement.

---

## 16. Glossary

| Term | Definition |
|------|-----------|
| **Flask** | Lightweight Python WSGI web framework used as the application backbone |
| **NLP** | Natural Language Processing — field of AI for understanding human language |
| **TF-IDF** | Term Frequency–Inverse Document Frequency — text vectorisation technique |
| **BERT** | Bidirectional Encoder Representations from Transformers — pre-trained language model |
| **F1-Score** | Harmonic mean of precision and recall used to evaluate classifier accuracy |
| **XGBoost** | Extreme Gradient Boosting — high-performance ensemble ML algorithm |
| **Celery** | Distributed task queue for Python, used here for async jobs |
| **JWT** | JSON Web Token — compact, URL-safe means of representing authentication claims |
| **Explainable AI** | Techniques that reveal why an ML model made a particular prediction |
| **Credibility Score** | Composite score (0–100%) indicating how likely an article is authentic |

---

## Document Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Manager | | | |
| Engineering Lead | | | |
| ML / Data Science Lead | | | |
| Security Lead | | | |
| Stakeholder / Sponsor | | | |

---

## Version History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | April 2026 | Product Team | Initial draft |

---

*This document is confidential and intended for internal use only.*
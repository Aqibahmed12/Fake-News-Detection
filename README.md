<div align="center">

# 🕵️ Real-Time Fake News Detection Platform

> A production-ready, lightning-fast NLP engine to identify misinformation and fact-check articles in milliseconds.

[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?logo=scikit-learn)](https://scikit-learn.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-%20-blue)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

At an era where misinformation spreads faster than truth, **Real-Time Fake News Detection** offers an API-first approach to content moderation and journalistic verification. Powered by advanced **Natural Language Processing (NLP)** and ensemble tree models, this platform analyzes structure, sentiment, and context to deliver actionable credibility metrics.

</div>

---

## ✨ Features

- **⚡ Lightning-Fast Inference**: Engineered on Flask + Gunicorn, returning results on complex texts in under `500ms`.
- **🧠 Explainable AI**: Doesn't just give a score—extracts and reveals the top 5 linguistic features (TF-IDF tokens, VADER sentiment, Flesch-Kincaid) contributing to the model's verdict.
- **🔄 Dual-Write Supabase Integration**: Seamlessly syncs your fact-checking history with a connected **PostgreSQL** Supabase instance for analytics, while gracefully falling back to local SQLite data structures during development.
- **🛡️ Secure & API-Ready**: Ready out of the gate with RESTful interfaces, JWT authentication, rate-limiting, and an elegant dashboard for monitoring queries.
- **🚀 Advanced Model Architecture**: Utilizes an orchestrated ML pipeline, defaulting to high-performance tree ensembles (XGBoost) with fallback paths for blazing rapid TF-IDF baseline regression.

## 🛠️ Architecture & Tech Stack

The architecture is explicitly designed for scale, readability, and modern cloud deployment frameworks:

* **Backend Framework**: Python / Flask
* **Machine Learning**: `scikit-learn`, `xgboost`, `spaCy`, `nltk`
* **Relational Data**: SQLAlchemy bridged to Supabase (PostgreSQL) or local SQLite
* **Frontend Analytics**: Jinja2 + Bootstrap 5 + interactive visual gauges
* **Security Layers**: Flask-JWT-Extended, Flask-Limiter

---

## 🚦 Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed and a virtual environment activated.

### 2. Installation Setup
Clone the repository, verify your configurations, and install the required dependencies:

```bash
# Clone the repository
git clone <repository_url>
cd <repository_folder>

# Install application dependencies via pip
pip install -r requirements.txt
```

### 3. Environment Configuration
Duplicate the provided example schema:
```bash
cp .env.example .env
```
Ensure you provide secure random strings for `SECRET_KEY` and `JWT_SECRET_KEY`. If utilizing the **Supabase** backend, populate your `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

### 4. Bootstrapping the Application
On the very first launch, the `MLEngine` checks its local cache. If the model hasn't been compiled down, it will dynamically train it in memory utilizing the onboard `DATA_DIR` artifacts.

```bash
python run.py
```

*The application will boot on `http://127.0.0.1:5000/`. You can navigate here to utilize the Web Dashboard.*

---

## 💻 API Reference Specification

Once deployed, query the unified endpoint seamlessly:

### **`POST /api/v1/detect`**

Authenticates your payload and evaluates the given text syntax.

**Request Body** (JSON):
```json
{
  "text": "BREAKING: Scientists have discovered an immortal species...",
  "return_features": true
}
```

**Successful Response** (`200 OK`):
```json
{
  "result_id": "cbf3214-...",
  "score": 0.82,
  "label": "LIKELY_REAL",
  "confidence": 0.91,
  "features": [...],
  "processing_ms": 114,
  "timestamp": "2026-04-20T08:30:00Z"
}
```

---

## 🛡️ Best Practices Implemented

- Strict modular codebases via Flask Blueprints (`app/api`, `app/web`).
- Secret Key encryption and OWASP top-10 defensive strategies enforced against injection/CSRF.
- CI/CD ready format.
- Abstracted ML components allowing seamless swapping of standard regression architectures with advanced Transformer neural networks without API layer disruption.

<div align="center">
<br/>
<em>Built for the protection of truth on the Digital Frontier.</em>
</div>

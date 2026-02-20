# Urdu Children's Story Generation System

A fully functional Urdu Story Generation AI App built using classical NLP techniques — n-gram language modeling, BPE tokenization, and modern software engineering practices including containerization and CI/CD.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Phase I: Dataset Collection and Preprocessing](#phase-i-dataset-collection-and-preprocessing)
- [Phase II: BPE Tokenizer Training](#phase-ii-bpe-tokenizer-training)
- [Phase III: Trigram Language Model](#phase-iii-trigram-language-model)
- [Phase IV: Microservice and Containerization](#phase-iv-microservice-and-containerization)
- [Phase V: Web-based Frontend](#phase-v-web-based-frontend)
- [Phase VI: Cloud Deployment](#phase-vi-cloud-deployment)
- [Project Structure](#project-structure)
- [How to Run Locally](#how-to-run-locally)

---

## Project Overview

This project implements a children's Urdu story generation system using a trigram probabilistic language model. The pipeline covers the full lifecycle from data scraping to a deployed web application.

| Phase | Description | Status |
|-------|-------------|--------|
| I | Dataset Collection & Preprocessing | Done |
| II | BPE Tokenizer Training | Done |
| III | Trigram Language Model | Done |
| IV | Microservice & Containerization | Done |
| V | Web-based Frontend | Done |
| VI | Cloud Deployment | Done |

---

## Phase I: Dataset Collection and Preprocessing

### What was done
- Scraped **200 Urdu children's stories** from UrduPoint Website
- Cleaned raw HTML: removed ads, tags, non-Urdu characters
- Normalized Unicode and standardized Urdu punctuation (۔ ، ؟ !)
- Injected special tokens at structural boundaries

### Special Tokens

Special tokens were added using unused Unicode Private Use Area characters to avoid conflicts with any standard Urdu characters:

| Token | Unicode | Purpose |
|-------|---------|---------|
| `<EOS>` | U+E000 | End of Sentence — added after ۔ ؟ ! |
| `<EOP>` | U+E001 | End of Paragraph — added at paragraph breaks |
| `<EOT>` | U+E002 | End of Text/Story — added at end of each story |

### Key File
- `p.py` — `SpecialTokenInjector` class that processes all story files and injects special tokens

---

## Phase II: BPE Tokenizer Training

### What was done
- Implemented a **custom Byte Pair Encoding (BPE) tokenizer from scratch** — no pre-built tokenizer libraries used
- Trained on the full preprocessed Urdu corpus
- Vocabulary size set to **250 tokens** as required

### How BPE Works (our implementation)
1. Start with individual characters as the base vocabulary
2. Count all adjacent token pairs in the corpus
3. Merge the most frequent pair into a new token
4. Repeat until vocabulary size reaches 250

### Output Files
- `bpe_tokenizer_v250_vocab.txt` — 250 vocabulary tokens
- `bpe_tokenizer_v250_merges.txt` — 170 merge operations learned during training

### Sample Vocabulary Entries
```
ایک</w>    # "ek" (one) as a complete word
اور</w>    # "aur" (and) as a complete word
کہ</w>     # "keh" (that) as a complete word
<EOS></w>  # End of sentence token
```

### Key File
- `bpe.py` — Full BPE training implementation

---

## Phase III: Trigram Language Model

### What was done
- Trained a **3-gram (trigram) language model** using Maximum Likelihood Estimation (MLE)
- Implemented **linear interpolation smoothing** to handle unseen contexts
- Supports variable-length generation until `<EOT>` token is reached

### Interpolation Formula

The probability of the next word is computed as a weighted combination:

```
P(w | w1, w2) = L3 * P_trigram(w | w1, w2)
              + L2 * P_bigram(w | w2)
              + L1 * P_unigram(w)
```

**Weights used:**
- L3 = 0.70 (trigram — highest weight, most context)
- L2 = 0.20 (bigram)
- L1 = 0.10 (unigram — fallback)

### Model Statistics
- Total tokens: **102,807**
- Vocabulary size: **11,810** unique tokens
- Trigram contexts: **57,423**

### Model Storage Format (trigram_model.json)
```json
{
  "meta": { "total_tokens": 102807, "vocab_size": 11810 },
  "unigram": { "word": count },
  "bigram":  { "w1": { "w2": count } },
  "trigram": { "w1|||w2": { "w3": probability } }
}
```

> Trigram keys use `|||` as separator (e.g. `"ایک|||دفعہ"`)

### Text Generation
Generation starts from a 2-word prefix and samples the next word using temperature-scaled probabilities until `<EOT>` is reached or `max_tokens` is hit.

### Key File
- `phase3_trigram_model.py` — Full model training, saving, loading, and generation

---

## Phase IV: Microservice and Containerization

### FastAPI Microservice

The trained trigram model is served via a **FastAPI REST microservice**.

**Base URL:** `http://localhost:8000`

#### Endpoints

**`POST /generate`** — Generate Urdu text from a prefix

Request:
```json
{
  "prefix": "ایک دفعہ",
  "max_tokens": 50
}
```

Response:
```json
{
  "generated_text": "ایک دفعہ کا ذکر ہے کہ ایک چھوٹا سا بچہ ..."
}
```

**`GET /health`** — Check service health

Response:
```json
{
  "status": "ok",
  "model_loaded": true,
  "trigram_contexts": 57423,
  "vocab_size": 11810
}
```

### Key File
- `phase4_microservice.py` — FastAPI app with model loading and inference

---

### Docker Containerization

The microservice is fully containerized using a **multi-stage Docker build**.

#### Dockerfile Features
- **Multi-stage build** — separate builder and runtime stages for a lean final image
- **Non-root user** — runs as `appuser` for security
- **Health check** — Docker monitors `/health` endpoint automatically
- **Environment variables** — `MODEL_PATH`, `MAX_TOKENS`, `TEMPERATURE` configurable at runtime

#### Build and Run
```bash
# Build the image
docker build -t urdu-api .

# Run the container
docker run -d -p 9000:8000 --name urdu-container urdu-api

# Open in browser
http://127.0.0.1:9000/docs
```

---

### GitHub Actions CI/CD Pipeline

Automated pipeline defined in `.github/workflows/ci-cd.yml` with 2 jobs:

**Job 1 — Lint & Test** (runs on every push and PR)
- Sets up Python 3.11
- Installs all dependencies
- Lints `phase4_microservice.py` with `flake8`
- Runs a live API smoke-test — starts the server and hits `/health`

**Job 2 — Build & Push Image** (runs after tests pass, on main branch only)
- Logs into GitHub Container Registry (GHCR)
- Builds the Docker image
- Pushes with smart tags: `latest`, branch name, short SHA

**Trigger Events:**
- Push to `main` or `develop`
- Pull requests to `main`
- Manual trigger via GitHub Actions UI

---

## Phase V: Web-based Frontend

A React/Next.js frontend that:
- Accepts a starting Urdu phrase from the user
- Displays step-wise story completion similar to ChatGPT
- Connects to the FastAPI backend

---

## Phase VI: Cloud Deployment

- **Frontend** — to be deployed on Vercel
- **Backend** — to be hosted on Render or Railway as a public container

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── ci-cd.yml                    # GitHub Actions CI/CD pipeline
│
└── Code/
    ├── Dockerfile                       # Multi-stage Docker build
    ├── requirements.txt                 # Python dependencies
    ├── p.py                             # Phase I: Special token injector
    ├── bpe.py                           # Phase II: BPE tokenizer training
    ├── bpe_tokenizer_v250_vocab.txt     # Trained vocabulary (250 tokens)
    ├── bpe_tokenizer_v250_merges.txt    # BPE merge operations (170 merges)
    ├── phase3_trigram_model.py          # Phase III: Trigram model
    ├── trigram_model.json               # Trained trigram model
    ├── phase4_microservice.py           # Phase IV: FastAPI microservice
    └── urdu_stories_tokenized/          # Preprocessed story corpus
```

---

## How to Run Locally

### Option 1 — Python directly

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python phase4_microservice.py

# Browser opens automatically at http://127.0.0.1:8001/docs
```

### Option 2 — Docker

```bash
# Build image
docker build -t urdu-api .

# Run container
docker run -d -p 9000:8000 --name urdu-container urdu-api

# Open http://127.0.0.1:9000/docs
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `./trigram_model.json` | Path to trained model file |
| `MAX_TOKENS` | `150` | Maximum tokens to generate |
| `TEMPERATURE` | `0.85` | Sampling temperature (higher = more creative) |

---

## Dependencies

```
fastapi
uvicorn
pydantic
```

---

## Authors

-- **Areesha Hussain**
-- **Shaheera Kashif**
-- **Syeda Irha Kazmi**

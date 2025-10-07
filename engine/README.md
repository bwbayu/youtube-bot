# Engine (Data & ML)

## Overview
The engine package hosts the offline tooling that powers Bot Judol: scraping YouTube comments, exploring and cleaning datasets, training IndoBERT-based classifiers, and benchmarking model deployments.

## Features
- Comment scraping workflow that batches YouTube Data API requests and persists results under `scraping/raw`.
- Data preparation helpers (e.g., `split_dataset.py`) that produce train, validation, and test CSV files with deterministic splits.
- Training script (`training.py`) that fine-tunes IndoBERT with Hugging Face Transformers, MLflow tracking, and GPU-aware configuration.
- Benchmark runner (`benchmark.py`) to measure inference latency and memory usage across CPU and CUDA devices.
- Exploratory notebook (`eda.ipynb`) for inspecting comment distributions and labeling outcomes.

## Repository Layout
- `data/` CSV datasets used during training and evaluation.
- `models/` exported PyTorch checkpoints such as `best_indobert.pt`.
- `scraping/` scripts and intermediate folders (`raw/`, `json/`, `clean/`) for ingestion pipelines.
- `training.py` primary fine-tuning entry point.
- `benchmark.py` inference performance harness.
- `split_dataset.py` reproducible dataset splitter.

## Environment Variables
- `API_KEY` YouTube Data API v3 key for unauthenticated comment scraping.
- `CLIENT_ID` Google OAuth client ID (optional; required if you expand scraping to use authorized requests).
- `CLIENT_SECRET` Google OAuth client secret (optional counterpart to the client ID).

Duplicate `engine/.env.example` to `engine/.env` and fill any values you plan to use. The `dotenv` loader is already wired into the scraping script.

## Setup
1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. (Optional) Install GPU-enabled PyTorch matching your CUDA version; the requirements file references the official cu126 wheel index. `pip3 install torch --index-url https://download.pytorch.org/whl/cu126`
4. Make sure `.env` contains a valid `API_KEY` and that the target video IDs are configured inside `scraping/main.py`.

## Common Tasks
- Run the scraper: `python scraping/main.py`.
- Split datasets: `python split_dataset.py`.
- Train IndoBERT: `python training.py` (logs metrics to MLflow if configured).
- Benchmark checkpoints: `python benchmark.py`.
- Inspect data: open `eda.ipynb` in Jupyter or VS Code.

## Notes
- Large checkpoints (`models/best_indobert.pt`, `models/best_roberta.pt`) are tracked in `models/` and consumed by the FastAPI service.
- Scraping requests are subject to YouTube API quotas; monitor your API key usage in Google Cloud Console.
- Scripts assume datasets live under `data/`; adjust paths if you externalize storage.

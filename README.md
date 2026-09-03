# Form 939 IDP - Cloud Evaluation Sandbox

This project evaluates LLMs (Local and Cloud) on extracting Israeli ID numbers from messy OCR text (Form 939).

## 🚀 How to run the Cloud Models (Your Task)

To get the real metrics (Latency, Cost, Accuracy) across the top cloud models, follow these steps:

### Step 1: Set up API Keys
1. Copy the `.env.example` file and rename it to `.env`.
2. Open `.env` and paste your API keys for Gemini, Anthropic (Claude), and DeepSeek.

### Step 2: Generate Advanced Synthetic Data
We have an advanced synthetic data generator that simulates real Hebrew OCR errors (like confusing `0` with `ם`, missing IDs, RTL issues).
Run this to generate a fresh batch of 20 test files:
```bash
python src/generate_synthetic.py
```

### Step 3: Run the Benchmark on Cloud Models
Run `main.py` and pass the cloud models you want to test. The script runs them concurrently (note: `max_concurrency=1` is set by default to prevent VRAM thrashing on local hardware, but this can be increased for cloud models in `main.py`).
```bash
python src/main.py --input-dir data/synthetic_inputs --gt-csv data/gold/synthetic_ground_truth.csv --models gemini/gemini-1.5-pro anthropic/claude-3-5-sonnet-20240620 deepseek/deepseek-chat
```

### Step 4: View the Dashboard
Once the benchmark finishes, generate the summary dashboard:
```bash
python src/dashboard.py
```
The results will be saved in `logs/dashboard.md` and printed to the console.

---
*Note: The default local models (`ollama/gemma4:e4b`, `ollama/llama3.1`, `ollama/qwen2.5:7b`) will be used if you run `python src/main.py` without the `--models` argument.*

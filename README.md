# CCKS2026 Steering Baseline

This repository contains a reproducible baseline pipeline for the CCKS2026 large model behavior steering task.

The implemented method is a contrastive activation addition baseline:

1. Group `train.json` by `concept_id`.
2. For every concept, compute hidden-state differences between `matching` and `not_matching` paired answers.
3. Average the differences into one steering vector per concept and layer.
4. During generation on `valid.json`, inject the matching concept vector into the selected transformer layer.

The pipeline does not use concept text in the generation prompt. The target behavior is applied through activation intervention.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Place the model locally if possible, then update `configs/baseline_caa.json`:

```json
{
  "model_name_or_path": "path/to/Qwen3-4B-Instruct-2507"
}
```

Using a local model path is recommended for repeatable runs.

## Commands

Inspect and validate data:

```powershell
python scripts/inspect_data.py --train train.json --valid valid.json --out runs/data_report.json
```

Check runtime and local model cache:

```powershell
python scripts/check_environment.py --config configs/baseline_caa.json --out runs/environment_report.json
```

Train CAA vectors:

```powershell
python scripts/train_vectors.py --config configs/baseline_caa.json
```

Generate validation predictions:

```powershell
python scripts/generate.py --config configs/baseline_caa.json
```

Smoke test the full pipeline on a tiny CPU model:

```powershell
python scripts/train_vectors.py --config configs/smoke_tiny_gpt2.json --limit-per-concept 1
python scripts/generate.py --config configs/smoke_tiny_gpt2.json --limit-per-concept 1
python scripts/local_eval.py --gold valid.json --pred runs/smoke_tiny_gpt2/predictions.json --out runs/smoke_tiny_gpt2/local_eval.json --allow-partial
python scripts/make_submission.py --pred runs/smoke_tiny_gpt2/predictions.json --out-dir runs/smoke_tiny_gpt2/submission
```

Run local proxy evaluation:

```powershell
python scripts/local_eval.py --gold valid.json --pred runs/baseline_caa/predictions.json --out runs/baseline_caa/local_eval.json
```

Create common submission variants:

```powershell
python scripts/make_submission.py --pred runs/baseline_caa/predictions.json --out-dir runs/baseline_caa/submission
```

The official Tianchi submission format should be checked on the competition page. This script writes JSON, JSONL, and CSV variants so the final packaging can be adapted quickly.

## No Validation Leakage

`scripts/train_vectors.py` only reads `train_path` from the config. `valid_path` is used only by generation and evaluation scripts.

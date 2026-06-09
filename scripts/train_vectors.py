from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from ccks_steering.chat import format_answer_chat, format_generation_prompt
from ccks_steering.config import load_config, resolve_output_dir, write_json
from ccks_steering.data import group_by_concept, load_records
from ccks_steering.modeling import torch_dtype_from_config, validate_runtime


@torch.inference_mode()
def answer_activation(model, tokenizer, question: str, answer: str, *, layer: int, max_length: int, pooling: str):
    prompt_text = format_generation_prompt(tokenizer, question)
    full_text = format_answer_chat(tokenizer, question, answer)
    prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
    encoded = tokenizer(full_text, return_tensors="pt", truncation=True, max_length=max_length)
    encoded = {key: value.to(model.device) for key, value in encoded.items()}

    outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    hidden = outputs.hidden_states[layer + 1][0]
    seq_len = hidden.shape[0]
    start = min(max(len(prompt_ids), 0), max(seq_len - 1, 0))
    answer_hidden = hidden[start:]
    if answer_hidden.numel() == 0:
        answer_hidden = hidden[-1:]

    if pooling == "answer_last":
        return answer_hidden[-1].detach().float().cpu()
    if pooling == "answer_mean":
        return answer_hidden.mean(dim=0).detach().float().cpu()
    if pooling == "sequence_mean":
        return hidden.mean(dim=0).detach().float().cpu()
    raise ValueError(f"Unsupported pooling: {pooling}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_caa.json")
    parser.add_argument("--limit-per-concept", type=int)
    args = parser.parse_args()

    config = load_config(args.config)
    validate_runtime(config)
    out_dir = resolve_output_dir(config)
    vector_dir = out_dir / "vectors"
    vector_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(config["train_path"])
    groups = group_by_concept(records)
    if args.limit_per_concept is not None:
        groups = {key: items[: args.limit_per_concept] for key, items in groups.items()}

    tokenizer = AutoTokenizer.from_pretrained(config["model_name_or_path"], trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        config["model_name_or_path"],
        torch_dtype=torch_dtype_from_config(config.get("dtype", "auto")),
        device_map=config.get("device_map", "auto"),
        trust_remote_code=True,
    )
    model.eval()

    metadata = {
        "config": config,
        "num_train_records": len(records),
        "num_concepts": len(groups),
        "limit_per_concept": args.limit_per_concept,
        "vectors": [],
    }
    max_length = int(config.get("max_length", 1024))
    pooling = config.get("pooling", "answer_mean")
    normalize = bool(config.get("normalize_vectors", True))

    for layer in config["layers"]:
        layer_vectors = {}
        for key, items in tqdm(sorted(groups.items(), key=lambda item: item[0].slug), desc=f"layer {layer}"):
            diffs = []
            for item in items:
                pos = answer_activation(
                    model,
                    tokenizer,
                    item["question"],
                    item["matching"],
                    layer=layer,
                    max_length=max_length,
                    pooling=pooling,
                )
                neg = answer_activation(
                    model,
                    tokenizer,
                    item["question"],
                    item["not_matching"],
                    layer=layer,
                    max_length=max_length,
                    pooling=pooling,
                )
                diffs.append(pos - neg)
            vector = torch.stack(diffs).mean(dim=0)
            norm = vector.norm().item()
            if normalize and norm > 0:
                vector = vector / norm
            layer_vectors[key.concept_id] = vector
            metadata["vectors"].append(
                {
                    "layer": layer,
                    "domain": key.domain,
                    "concept_id": key.concept_id,
                    "concept": key.concept,
                    "num_examples": len(items),
                    "pre_normalization_norm": norm,
                }
            )
        torch.save(layer_vectors, vector_dir / f"layer_{layer}.pt")

    write_json(out_dir / "vector_metadata.json", metadata)
    print(f"Wrote vectors to {vector_dir}")
    print(json.dumps({"layers": config["layers"], "concepts": len(groups)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

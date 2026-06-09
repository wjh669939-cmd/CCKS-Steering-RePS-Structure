from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

from ccks_steering.chat import format_generation_prompt, strip_thinking
from ccks_steering.config import load_config, resolve_output_dir, write_json
from ccks_steering.data import group_by_concept, load_records
from ccks_steering.modeling import steering_hook, torch_dtype_from_config, validate_runtime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/baseline_caa.json")
    parser.add_argument("--layer", type=int)
    parser.add_argument("--strength", type=float)
    parser.add_argument("--limit-per-concept", type=int)
    parser.add_argument("--out")
    args = parser.parse_args()

    config = load_config(args.config)
    validate_runtime(config)
    out_dir = resolve_output_dir(config)
    gen_config = dict(config.get("generation", {}))
    layer = int(args.layer if args.layer is not None else gen_config.get("layer", config["layers"][0]))
    strength = float(args.strength if args.strength is not None else gen_config.get("strength", 1.0))
    apply_to = gen_config.get("apply_to", "last")
    seed = gen_config.get("seed")
    if seed is not None:
        set_seed(int(seed))

    vector_path = out_dir / "vectors" / f"layer_{layer}.pt"
    vectors = torch.load(vector_path, map_location="cpu")
    records = load_records(config["valid_path"])
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
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    generation_kwargs = {
        "max_new_tokens": int(gen_config.get("max_new_tokens", 160)),
        "temperature": float(gen_config.get("temperature", 0.7)),
        "top_p": float(gen_config.get("top_p", 0.9)),
        "do_sample": bool(gen_config.get("do_sample", True)),
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }

    predictions = []
    for key, items in tqdm(sorted(groups.items(), key=lambda item: item[0].slug), desc="generate"):
        if key.concept_id not in vectors:
            raise KeyError(f"No vector found for concept_id={key.concept_id} in {vector_path}")
        vector = vectors[key.concept_id]
        with steering_hook(model, layer=layer, vector=vector, strength=strength, apply_to=apply_to):
            for item in items:
                prompt = format_generation_prompt(tokenizer, item["question"])
                encoded = tokenizer(prompt, return_tensors="pt").to(model.device)
                output_ids = model.generate(**encoded, **generation_kwargs)
                new_tokens = output_ids[0, encoded["input_ids"].shape[1] :]
                answer = strip_thinking(tokenizer.decode(new_tokens, skip_special_tokens=True))
                predictions.append(
                    {
                        "domain": item["domain"],
                        "concept_id": item["concept_id"],
                        "concept": item["concept"],
                        "question_id": item["question_id"],
                        "question": item["question"],
                        "answer": answer,
                        "layer": layer,
                        "strength": strength,
                    }
                )

    out_path = Path(args.out) if args.out else out_dir / "predictions.json"
    write_json(out_path, predictions)
    print(f"Wrote {out_path}")
    print(json.dumps({"records": len(predictions), "layer": layer, "strength": strength}, ensure_ascii=False))


if __name__ == "__main__":
    main()

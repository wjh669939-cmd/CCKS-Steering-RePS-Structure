from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import torch


def validate_runtime(config: dict) -> None:
    if config.get("require_cuda", False) and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available, but config requires it. "
            "Qwen3-4B steering is not practical on CPU. "
            "Use a CUDA PyTorch environment or set require_cuda=false for smoke tests."
        )


def torch_dtype_from_config(dtype: str):
    if dtype in ("auto", None):
        return "auto"
    mapping = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    if dtype not in mapping:
        raise ValueError(f"Unsupported dtype: {dtype}")
    return mapping[dtype]


def resolve_decoder_layers(model):
    candidates = [
        ("model", "layers"),
        ("transformer", "h"),
        ("gpt_neox", "layers"),
    ]
    for first, second in candidates:
        parent = getattr(model, first, None)
        if parent is not None and hasattr(parent, second):
            return getattr(parent, second)
    if hasattr(model, "model") and hasattr(model.model, "decoder") and hasattr(model.model.decoder, "layers"):
        return model.model.decoder.layers
    raise AttributeError("Could not locate decoder layers on this model")


@contextmanager
def steering_hook(model, *, layer: int, vector: torch.Tensor, strength: float, apply_to: str) -> Iterator[None]:
    layers = resolve_decoder_layers(model)
    if layer < 0 or layer >= len(layers):
        raise ValueError(f"Layer {layer} out of range; model has {len(layers)} layers")

    def hook(_module, _inputs, output):
        hidden = output[0] if isinstance(output, tuple) else output
        steer = vector.to(device=hidden.device, dtype=hidden.dtype) * strength
        if apply_to == "last":
            hidden = hidden.clone()
            hidden[:, -1, :] = hidden[:, -1, :] + steer
        elif apply_to == "all":
            hidden = hidden + steer.view(1, 1, -1)
        else:
            raise ValueError(f"Unsupported apply_to: {apply_to}")
        if isinstance(output, tuple):
            return (hidden,) + output[1:]
        return hidden

    handle = layers[layer].register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()

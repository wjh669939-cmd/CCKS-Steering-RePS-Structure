from __future__ import annotations


def format_generation_prompt(tokenizer, question: str) -> str:
    messages = [{"role": "user", "content": question}]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except (TypeError, ValueError):
            return f"User: {question}\nAssistant:"
    return f"User: {question}\nAssistant:"


def format_answer_chat(tokenizer, question: str, answer: str) -> str:
    messages = [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
                enable_thinking=False,
            )
        except (TypeError, ValueError):
            return f"User: {question}\nAssistant: {answer}"
    return f"User: {question}\nAssistant: {answer}"


def strip_thinking(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>", 1)[1].strip()
    return text.strip()

# model_utils.py
from functools import lru_cache
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME       = "google/gemma-3-1b-it"
MAX_NEW_TOKENS   = 2048
TEMPERATURE      = 0.5
TOP_P            = 0.9


@lru_cache                 # ──> загрузится ровно один раз
def load_model():
    tok = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, device_map="auto", torch_dtype="auto"
    )
    mdl.eval()
    return tok, mdl


def _sample_next(logits, *, temperature=TEMPERATURE, top_p=TOP_P):
    logits = logits.squeeze(0) / temperature
    probs  = torch.softmax(logits, dim=-1)

    sorted_probs, sorted_idx = torch.sort(probs, descending=True)
    cumsum = torch.cumsum(sorted_probs, dim=-1)
    cut    = torch.searchsorted(cumsum, top_p).item()
    sorted_probs[cut + 1:] = 0
    sorted_probs /= sorted_probs.sum()

    next_token = torch.multinomial(sorted_probs, 1)
    return sorted_idx[next_token]


def generate_once(prompt: str) -> str:
    """
    Генерирует полный ответ нейросети за один вызов.
    """
    tok, mdl = load_model()

    # Преобразуем входной текст в тензоры
    input_ids = tok(prompt, return_tensors="pt").input_ids.to(mdl.device)

    # Генерация текста
    with torch.no_grad():
        output_ids = mdl.generate(
            input_ids,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            eos_token_id=tok.eos_token_id,
        )

    # Декодируем сгенерированный текст
    generated_text = tok.decode(output_ids[0], skip_special_tokens=True)
    return generated_text

# model_utils.py
from functools import lru_cache
import torch
from peft import PeftModel
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

BASE_MODEL_NAME       = "google/gemma-3-1b-it"
ADAPTER_PATH   = "fine-tuned-gemma"
MAX_NEW_TOKENS   = 512
TEMPERATURE      = 0.5
TOP_P            = 0.9


# Квант-конфиг для 4-битной загрузки
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)


@lru_cache                 # ──> загрузится ровно один раз
def load_model():
    # токенизатор
    tokenizer = AutoTokenizer.from_pretrained(
        ADAPTER_PATH,
        use_fast=True,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # gemma 3 с квант-конфигом
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        device_map="auto",
        quantization_config=bnb_config,
        trust_remote_code=True,
    )
    base_model.eval()

    # base_model + LoRA-адаптер
    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_PATH,
        device_map="auto",
        torch_dtype=torch.float16,  # или auto
    )
    model.eval()

    return tokenizer, model


def generate_once(prompt: str) -> str:
    """
    Генерирует полный ответ нейросети за один вызов.
    """
    tok, mdl = load_model()

    # Преобразуем входной текст в тензоры
    inputs = tok(prompt, return_tensors="pt").to(mdl.device)

    # Генерация текста
    with torch.no_grad():
        output_ids = mdl.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            eos_token_id=tok.eos_token_id,
        )

    # Декодируем сгенерированный текст
    generated_text = tok.decode(output_ids[0], skip_special_tokens=True)
    return generated_text


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

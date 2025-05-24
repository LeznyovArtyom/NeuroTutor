import os
from functools import lru_cache
import torch
from huggingface_hub import login
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


# Авторизация в HuggingFace
# HF_TOKEN = os.getenv("HF_TOKEN")
# if HF_TOKEN:
login("...")


BASE_MODEL_NAME = "google/gemma-3-1b-it"
ADAPTER_PATH    = "fine-tuned-gemma"

MAX_NEW_TOKENS  = 512
TEMPERATURE     = 0.5
TOP_P           = 0.9


# Однократная (кэшированная) загрузка
@lru_cache
def load_model():
    """
    Возвращает (tokenizer, model). Загружается один раз на процесс.
    Если запущено через gunicorn --preload, память не копируется.
    """
    # токенизатор
    tokenizer = AutoTokenizer.from_pretrained(
        ADAPTER_PATH,
        use_fast=True,
        trust_remote_code=True,
    )
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

    # базовая Gemma
    dtype  = torch.bfloat16          # экономит ×2 RAM на CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=dtype,
        device_map="auto",            # на CPU – просто «cpu»
        low_cpu_mem_usage=True,       # загружает блоками → меньше пик RAM
        trust_remote_code=True,
    )
    base.eval()

    # LoRA-адаптер
    model = PeftModel.from_pretrained(
        base,
        ADAPTER_PATH,
        torch_dtype=dtype,
        device_map="auto",
    )
    model.eval()

    return tokenizer, model


# Функция генерации
def generate_once(prompt: str) -> str:
    """
    Генерирует полный ответ модели (без стриминга).
    """
    tok, mdl = load_model()

    inputs = tok(prompt, return_tensors="pt").to(mdl.device)

    with torch.no_grad():
        out_ids = mdl.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            eos_token_id=tok.eos_token_id,
        )

    return tok.decode(out_ids[0], skip_special_tokens=True)




# Обращение к модели Mistral по API
from mistralai import Mistral


MISTRAL_MODEL   = "mistral-small-latest"
MAX_NEW_TOKENS  = 512
TEMPERATURE     = 0.5
TOP_P           = 0.9


async def generate_once_mistral(prompt: str) -> str:
    api_key = os.getenv("MISTRAL_API_KEY", "...")
    client  = Mistral(api_key=api_key)

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Mistral возвращает сразу один choice
    return response.choices[0].message.content.strip()

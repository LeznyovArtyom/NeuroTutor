import os, aiohttp, asyncio
from functools import lru_cache
from huggingface_hub import login
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from mistralai import Mistral
import llm_config


# Однократная (кэшированная) загрузка модели из Hugging Face
@lru_cache
def load_model():
    """
    Возвращает (tokenizer, model). Загружается один раз на процесс.
    Если запущено через gunicorn --preload, память не копируется.
    """
    # токенизатор
    tokenizer = AutoTokenizer.from_pretrained(
        llm_config.ADAPTER_PATH,
        use_fast=True,
        trust_remote_code=True,
    )
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token

    # базовая Gemma
    dtype  = torch.bfloat16          # экономит ×2 RAM на CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"

    base = AutoModelForCausalLM.from_pretrained(
        llm_config.BASE_MODEL_NAME,
        torch_dtype=dtype,
        device_map="auto",            # на CPU – просто «cpu»
        low_cpu_mem_usage=True,       # загружает блоками → меньше пик RAM
        trust_remote_code=True,
    )
    base.eval()

    # LoRA-адаптер
    model = PeftModel.from_pretrained(
        base,
        llm_config.ADAPTER_PATH,
        torch_dtype=dtype,
        device_map="auto",
    )
    model.eval()

    return tokenizer, model


# Обращение к дообученной локальной модели
def generate_once_base_model(prompt: str) -> str:
    """
    Генерирует полный ответ модели (без стриминга).
    """
    # Авторизация в HuggingFace
    login(llm_config.HF_TOKEN)

    tok, mdl = load_model()

    inputs = tok(prompt, return_tensors="pt").to(mdl.device)

    with torch.no_grad():
        out_ids = mdl.generate(
            **inputs,
            max_new_tokens=llm_config.MAX_NEW_TOKENS,
            temperature=llm_config.TEMPERATURE,
            top_p=llm_config.TOP_P,
            eos_token_id=tok.eos_token_id,
        )

    return tok.decode(out_ids[0], skip_special_tokens=True)


# Обращение к модели Mistral по API
async def generate_once_mistral(prompt: str) -> str:
    client  = Mistral(api_key=llm_config.MISTRAL_API_KEY)

    response = client.chat.complete(
        model=llm_config.MISTRAL_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Mistral возвращает сразу один choice
    return response.choices[0].message.content.strip()


# Обращение к модели YandexGPT Lite по API
async def generate_once_yagpt(prompt: str) -> str:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Authorization": f"Bearer {llm_config.IAM_TOKEN}",
        "Content-Type":  "application/json",
        "X-Folder-Id":   llm_config.FOLDER_ID,
    }

    body = {
        "modelUri": f"gpt://{llm_config.FOLDER_ID}/{llm_config.YANDEX_MODEL}/latest",

        "completionOptions": {
            "stream": False,
            "temperature": llm_config.TEMPERATURE,
            "maxTokens":  llm_config.MAX_NEW_TOKENS
        },

        "messages": [
            {"role": "user", "text": prompt}
        ]
    }

    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=body, headers=headers) as r:
            r.raise_for_status()
            data = await r.json()

    return data["result"]["alternatives"][0]["message"]["text"].strip()


# Сгенерировать ответ в соответствии с выбранно моделью
async def generate_once(prompt: str) -> str:
    if llm_config.CURRENT_MODEL == "base":
        return await generate_once_base_model(prompt)

    if llm_config.CURRENT_MODEL == "mistral":
        return await generate_once_mistral(prompt)

    if llm_config.CURRENT_MODEL == "yandex":
        return await generate_once_yagpt(prompt)
    
    return


# Тест YandexGPT
if __name__ == "__main__":
    async def _demo():
        print(await generate_once_yagpt("Привет! Скажи что-нибудь."))
    asyncio.run(_demo())

import os, aiohttp, asyncio
from functools import lru_cache
from huggingface_hub import login
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from mistralai import Mistral
import llm.llm_config as llm_config
from llm.RAG.rag_retrieve import retrieve
from database.sql_models import Work as WorkModel, ModelType
from sqlmodel import Session


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


# Сгенерировать ответ с базовой моделью
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


# Сгенерировать ответ с дообученной моделью
def generate_once_finetuned(prompt: str) -> str:
    return generate_once_base_model(prompt)


# Общая функция для формирования RAG-промпта
def build_rag_prompt(prompt_text: str, work: WorkModel, session: Session) -> str:
    """
    1) Извлекаем из work список документов и section
    2) Получаем RAG-контекст через retrieve(...)
    3) Склеиваем контекст + исходный prompt_text
    """
    discipline_id = work.discipline_id
    doc_ids       = [d.id for d in work.documents] or None
    section       = work.document_section or None

    context = retrieve(
        question      = prompt_text,
        session       = session,
        discipline_id = discipline_id,
        scope_docs    = doc_ids,
        scope_section = section
    )

    full_prompt = (
        "Ты цифровой преподаватель. Используй КОНТЕКСТ ниже, чтобы сгенерировать ответ.\n\n"
        f"КОНТЕКСТ:\n{context}\n\n"
        f"ВОПРОС:\n{prompt_text}"
    )
    return full_prompt


# Сгенерировать ответ с базовой моделью + RAG
async def generate_once_rag(prompt_text: str, work: WorkModel, session: Session) -> str:
    full_prompt = build_rag_prompt(prompt_text, work, session)
    return generate_once_base_model(full_prompt)


# Сгенерировать ответ с дообученной моделью + RAG
async def generate_once_finetuned_rag(prompt_text: str, work: WorkModel, session: Session) -> str:
    full_prompt = build_rag_prompt(prompt_text, work, session)
    return await generate_once_finetuned(full_prompt)


# Сгенерировать ответ в соответствии с выбранным типом модели
async def generate_once(prompt: str, work: WorkModel | None = None, session: Session | None = None) -> str:
    """
    В зависимости от work.model_type выбираем один из 4 режимов:
        - base            → базовая (без дообучения, без RAG)
        - fine_tuned      → дообученная (LoRA или подобная)
        - rag             → базовая + RAG
        - fine_tuned_rag  → дообученная + RAG
    """
    return await generate_once_yagpt(prompt)
    mode = work.model_type

    if mode == ModelType.BASE:
        return await generate_once_base_model(prompt)

    if mode == ModelType.FINE_TUNED:
        return await generate_once_finetuned(prompt)

    if mode == ModelType.RAG:
        return await generate_once_rag(prompt, work, session)

    if mode == ModelType.FINE_TUNED_RAG:
        return await generate_once_finetuned_rag(prompt, work, session)

    raise RuntimeError(f"Неизвестный режим модели: {mode}")


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


# Тест YandexGPT
if __name__ == "__main__":
    async def _demo():
        print(await generate_once_yagpt("Привет! Скажи что-нибудь."))
    asyncio.run(_demo())

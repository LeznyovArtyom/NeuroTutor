from typing import List
from nltk.metrics import edit_distance
import json, re, os, asyncio
from models import Chat as ChatModel, ChatStage, Work as WorkModel
from sqlmodel import Session
import PyPDF2
import docx # python-docx
from pathlib import Path
from io import BytesIO
from model_utils import generate_once_mistral


# Извлечение текста из PDF / DOCX / TXT
def extract_text(file_data: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower() # Приведение расширения к нижнему регистру
    try:
        if ext == ".pdf":
            pdf = PyPDF2.PdfReader(BytesIO(file_data), strict=False)
            raw = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext in {".docx", ".doc"}:
            doc = docx.Document(BytesIO(file_data))
            raw = "\n".join(p.text for p in doc.paragraphs)
        elif ext in {".txt", ".md"}:
            raw = file_data.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"Неподдерживаесый типа файла: {ext}")
    except Exception as error:
        raise RuntimeError(f"Произошла ошибка извлечения текста из файла {filename}: {error}")
    
    # нормализация
    cleaned = re.sub(r"[ \t]+", " ", raw)
    cleaned = re.sub(r"\s*\n\s*", "\n", cleaned)
    return cleaned.strip()


# Один шаг проверки работы цифрового помощника
async def next_turn(chat: ChatModel, user_message: str | None, session: Session) -> str:
    """
    Выполняет один шаг проверки работы:
    - На этапе UPLOAD: формирует промпт для LLM, содержащий текст отчёта и ожидаемое задание,
      получает от модели JSON-оценку, парсит её и возвращает соответствующий ответ.
    - Далее: как раньше, вопрос-ответ.
    """
    # 0. Чат создан, работа не загружена
    if chat.stage == ChatStage.NEW:
        return "Пожалуйста, загрузите файл с работой, чтобы я мог приступить к проверке."
    
    # 2. Попросить загрузить исправленную работу
    if chat.stage == ChatStage.RETURNED_FOR_REVISION:
        return "Вашу работу вернули на доработку. Пожалуйста, загрузите исправленную версию."


    

    # ---------- 2. диалог DIALOGUE ----------
    if chat.stage == ChatStage.DIALOGUE:
        meta = json.loads(chat.meta)
        qinfo = meta["qs"][chat.current_q]
        score = grade(user_message, qinfo["a"])
        chat.score += score
        correct = score > 0.8

        if correct:
            feedback = "Верно! ✅"
            chat.current_q += 1
        else:
            # уточняем / переспрашиваем
            if score > 0.4:
                feedback = "Почти! Попробуйте уточнить 🤔"
                session.add(chat); session.commit()
                return feedback          # задаём тот же вопрос ещё раз
            feedback = f"Неверно. Правильный ответ: {qinfo['a']}"

        # все вопросы закончились?
        if chat.current_q == len(meta["qs"]):
            chat.stage = ChatStage.REVIEW
        else:
            # при необходимости повышаем сложность
            nxt = meta["qs"][chat.current_q]
            feedback += f"\n\nВопрос {chat.current_q+1}: {nxt['q']}"

        session.add(chat); session.commit()
        return feedback

    # ---------- 3. формирование статистики ----------
    if chat.stage == ChatStage.REVIEW:
        n = len(json.loads(chat.meta)["qs"])
        result = chat.score / n
        chat.stage = ChatStage.FINISHED
        session.add(chat); session.commit()
        if result >= 0.8:
            return f"Работа зачтена («{result*100:.0f}%»)! 🎉"
        return (f"Работа не зачтена ({result*100:.0f}%). "
                "Советую повторить тему X и Y.")

    # ---------- 4. всё кончилось ----------
    return "Сессия завершена. Создайте новый чат, если нужны вопросы."


# 1. проверка работы
async def handle_checking_the_work_stage(chat: ChatModel, session: Session) -> str:
    # извлекаем текст из загруженного файла
    if not chat.document_data or not chat.document_name:
        raise RuntimeError("Документ или имя документа не установлены для чата")
    file_text = extract_text(chat.document_data, chat.document_name)

    # получаем описание задания из работы
    work: WorkModel = session.get(WorkModel, chat.work_id)
    expected_task = work.task or ""
    
    # формируем промпт для оценки правильности
    system_prompt = (
        "Ты выступаешь в роли цифрового преподавателя. Оцени работу студента. Проверь, выполнено ли студентом задание, описанное ниже. "
        f"Описание задания: {expected_task}\n"
        "Игнорируй остальные части отчёта; оцени только выполнение пунктов задания. "
        "Верни объект JSON с ключами: "
        "'status' ('ok' или 'needs_fix'), "
        "'feedback' (краткое описание строки), "
        "'missing' (массив строк, необязательно), "
        "'questions' (массив из {'q','a'}, только если статус 'ok')."
    )
    user_prompt = (
        f"Описание задания: {expected_task}\n"
        f"Текст отчета:\n{file_text}"
    )
    full_prompt = system_prompt + "\n\n" + user_prompt
    # запрос к модели
    resp = await generate_once_mistral(full_prompt)

    # вырезаем JSON markdown из ответа
    text = resp.strip()
    if match := re.search(r"```(?:json)?\n([\s\S]*?)```", text):
        text = match.group(1).strip()
    text = re.sub(r"^json\s*", "", text, flags=re.IGNORECASE).strip()

    # парсим JSON
    try:
        result = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Ошибка парсинга JSON: {error}\nОтвет: {text}")
    status = result.get('status')
    feedback = result.get('feedback', '')
    missing = result.get('missing', []) or []

    # Сохраним исходный текст и список недоработок
    chat.meta = json.dumps({
        "original_excerpt": file_text,
        "missing": missing
    })

    # Если работает требует доработки
    if status != 'ok':
        message = f"❌ Работа требует доработки: {feedback}"
        if missing:
            message += "\n\nНедоработки:" + "\n" + "\n".join(f"- {item}" for item in missing)
        chat.stage = ChatStage.RETURNED_FOR_REVISION
        session.add(chat)
        session.commit()
        return message
    


    # Если работа правильная
    questions = result.get('questions', [])
    chat.meta = json.dumps({'status': 'ok', 'feedback': feedback, 'questions': questions})
    chat.stage = ChatStage.DIALOGUE
    chat.current_q = 0
    session.add(chat); session.commit()
    first_q = questions[0]['q'] if questions else 'Опишите, что вы сделали в работе.'
    return f"✅ В работе нет недочетов ({feedback}). Начинаем самопроверку:\n\nВопрос 1: {first_q}"


# 2. проверка исправленной работы
async def handle_checking_the_corrected_work_stage(chat: ChatModel, session: Session) -> str:
    # извлекаем текст из загруженного файла
    if not chat.document_data or not chat.document_name:
        raise RuntimeError("Документ или имя документа не установлены для чата")
    new_text = extract_text(chat.document_data, chat.document_name)

    # достаём сохранённый в chat.meta старый результат с missing и оригинальный текст
    data = json.loads(chat.meta)
    original_excerpt = data.get('original_excerpt', '') # Данные предыдущей загруженной работы
    missing = data.get('missing', []) # Недоработки

    # получаем описание задания из работы
    work: WorkModel = session.get(WorkModel, chat.work_id)
    expected_task = work.task or ""
    
    # промпт сравнения
    system_prompt = (
        "Ты — цифровой преподаватель. "
        "Описание задания:\n" + expected_task + "\n\n"
        "Ранее ты нашёл в этой работе следующие недоработки в отчете:\n" +
        "\n".join(f"- {m}" for m in missing) +
        "\nТеперь студент загрузил исправленную версию. "
        "Проверь, были ли эти недоработки устранены. "
        "Верни строго JSON с полями:\n"
        "  fixed: true или false,\n"
        "  missing: [массив оставшихся недоработок],\n"
        "  feedback: \"краткий комментарий\".\n"
        "  questions: (массив из {'q','a'}, только если fixed = true).\n"
    )
    user_prompt = (
        "Старая версия отчёта:\n" + original_excerpt + "\n\n"
        "Новая версия отчёта:\n" + new_text
    )
    full_prompt = system_prompt + "\n\n" + user_prompt
    # запрос к модели
    resp = await generate_once_mistral(full_prompt)

    # вырезаем JSON markdown из ответа
    text = resp.strip()
    if match := re.search(r"```(?:json)?\n([\s\S]*?)```", text):
        text = match.group(1).strip()
    text = re.sub(r"^json\s*", "", text, flags=re.IGNORECASE).strip()

    # парсим JSON
    try:
        result = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Ошибка парсинга JSON: {error}\nОтвет: {text}")
    
    fixed = result.get("fixed", False)
    still_missing = result.get("missing", [])
    
    if not fixed:
        # перезаписываем meta для следующей итерации
        chat.meta = json.dumps({
            "original_excerpt": original_excerpt,
            "missing": still_missing
        })
        chat.stage = ChatStage.RETURNED_FOR_REVISION
        session.add(chat)
        session.commit()
        return "❌ Всё ещё есть недоработки:\n" + "\n".join(f"- {m}" for m in still_missing)
        
    # если fixed==true — запустить Q&A
    questions = result.get('questions', [])
    chat.meta = json.dumps({ 
        'status': 'ok', 
        'feedback': result['feedback'], 
        'questions': questions 
    })
    chat.stage = ChatStage.DIALOGUE
    chat.current_q = 0
    session.add(chat)
    session.commit()
    return f"✅ Всё исправлено ({result['feedback']}). Начинаем самопроверку:\n\nВопрос 1: {questions[0]['q']}"

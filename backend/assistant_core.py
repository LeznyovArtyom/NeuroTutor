import json, re
from models import Chat as ChatModel, ChatStage, Work as WorkModel, UserWork as UserWorkModel, WorkStatus
from sqlmodel import Session, select
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


# Обновление статуса сдачи работы студентом
def set_user_work_status(chat: ChatModel, session: Session, new_status: WorkStatus) -> None:
    """
    Обновляет статус сдачи *для конкретного студента и работы*,
    к которой привязан чат.
    """
    user_work = session.exec(
        select(UserWorkModel)
        .where(UserWorkModel.student_id == chat.user_id,
               UserWorkModel.work_id    == chat.work_id)
    ).first()
    if user_work and user_work.status != new_status:
        user_work.status = new_status
        session.add(user_work)
        session.commit()


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
        set_user_work_status(chat, session, WorkStatus.NEED_FIX)
        session.add(chat)
        session.commit()
        return message
    
    # Работа корректна - нужно начать dualogue
    # Просим модель сгенерировать один стартовый вопрос
    sys = (
        "Ты — цифровой преподаватель. "
        "На основе отчёта сформируй ОДИН простой контрольный вопрос "
        "и выпиши список ключевых тем (3-7 пунктов, в терминах предмета). "
        "Верни JSON: {question, answer, topics:[...]}"
    )
    raw = await generate_once_mistral(sys + "\n\n" + file_text)
    data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))

    chat.meta = json.dumps({
        "task": expected_task,
        "topics": data["topics"],
        "stats": {"asked": 0, "correct": 0},
        "last_q": data["question"],
        "last_a": data["answer"],
    })
    chat.stage = ChatStage.DIALOGUE
    session.add(chat)
    session.commit()

    return (f"✅ В работе нет недочётов ({feedback}). Переходим к опросу!\n\n Вопрос 1: {data['question']}")


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
            "original_excerpt": new_text, # Ложим текущую версию работы
            "missing": still_missing
        })
        chat.stage = ChatStage.RETURNED_FOR_REVISION
        set_user_work_status(chat, session, WorkStatus.NEED_FIX)
        session.add(chat)
        session.commit()
        return "❌ Всё ещё есть недоработки:\n" + "\n".join(f"- {m}" for m in still_missing)
        
    # Работа корректна - нужно начать dualogue
    # Просим модель сгенерировать один стартовый вопрос
    sys = (
        "Ты — цифровой преподаватель. "
        "На основе отчёта сформируй ОДИН простой контрольный вопрос "
        "и выпиши список ключевых тем (3-7 пунктов, в терминах предмета). "
        "Верни JSON: {question, answer, topics:[...]}"
    )
    raw = await generate_once_mistral(sys + "\n\n" + new_text)
    data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))

    chat.meta = json.dumps({
        "task": expected_task,
        "topics": data["topics"],
        "stats": {"asked": 0, "correct": 0},
        "last_q": data["question"],
        "last_a": data["answer"],
    })
    chat.stage = ChatStage.DIALOGUE
    session.add(chat)
    session.commit()
    return f"✅ Всё исправлено ({result['feedback']}). Начинаем самопроверку:\n\nВопрос 1: {data['question']}"


MAX_ATTEMPTS = 2          # сколько попыток давать на один вопрос
SCORE_PARTIAL = 0.5       # балл за частично-верный ответ


# 3. Диалог между помощником и студентом в формате вопрос-ответ
async def dialogue(chat: ChatModel, user_message: str | None, session: Session) -> str:
    # Подгружаем данные meta
    meta = json.loads(chat.meta or "{}")
    stats = meta["stats"]
    tries  = meta.get("attempts", 0)  # сколько попыток по текущему вопросу

    # ---------- 1. просим LLM оценить ответ ----------
    sys_prompt = (
        "Ты — цифровой преподаватель. "
        "Оцени ответ студента на предыдущий вопрос и реши, "
        "нужен ли уточняющий/наводящий вопрос.\n"
        "Верни СТРОГО JSON вида:\n"
        "{quality:'correct'|'partial'|'wrong', "
        " feedback:str, "
        " follow_up?:str  # если нужно уточнить}"
    )
    user_prompt = json.dumps({
        "question"     : meta["last_q"],
        "right_answer" : meta["last_a"],
        "student_answer": user_message,
        "tries_done"   : tries
    }, ensure_ascii=False)
    raw = await generate_once_mistral(sys_prompt + "\n\n" + user_prompt)
    result = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))

    quality   = result["quality"] # correct | partial | wrong
    feedback  = result["feedback"]
    follow_up = result.get("follow_up", "")

    # ---------- 2. решение: остаться на вопросе либо перейти к следующему ----------
    #  а) ещё есть попытки и ответ не «correct»  ➜ остаёмся
    if quality != "correct" and tries < MAX_ATTEMPTS:
        meta["attempts"] = tries + 1
        chat.meta = json.dumps(meta)
        session.add(chat)
        session.commit()
        hint = follow_up or "Попробуйте уточнить свой ответ."
        return f"{feedback}\n\n{hint}"

    #  б) вопрос заканчивается (учтём статистику и баллы)
    stats["asked"]   += 1
    if quality == "correct":
        stats["correct"] += 1
    elif quality == "partial":
        stats["correct"] += SCORE_PARTIAL

    meta["attempts"] = 0  # обнуляем попытки для следующего вопроса

    # ---------- 3. остались ли ещё темы / вопросы ----------
    topics_left = meta["topics"]
    if not topics_left:
        # Все темы спрашивали → подводим итог
        chat.stage = ChatStage.FINISHED
        passed = stats["correct"] / stats["asked"] >= 0.8
        set_user_work_status(
            chat, session,
            WorkStatus.PASSED if passed else WorkStatus.FAILED
        )
        session.add(chat)
        session.commit()
        verdict = "Работа зачтена! 🎉" if passed else "Работа не зачтена."
        return f"{feedback}\n\n{verdict}"
    
    # ---------- 4. генерируем следующий вопрос ----------
    next_topic = topics_left.pop(0)
    q_prompt = (
        "Сформулируй один проверочный вопрос по теме: " + next_topic +
        "\nВерни JSON: {q, a}"
    )
    qa_raw = await generate_once_mistral(q_prompt)
    qa = json.loads(re.search(r"\{.*\}", qa_raw, re.S).group(0))

    # Обновляем meta
    meta.update({
        "stats" : stats,
        "last_q": qa["q"],
        "last_a": qa["a"],
        "topics": topics_left
    })
    chat.meta = json.dumps(meta)
    session.add(chat); session.commit()

    return f"{feedback}\n\nВопрос: {qa['q']}"
import faiss, numpy as np
from sqlmodel import Session, select
from models import DocumentChunk, Document
from RAG.utils import embed


# one-time: собираем FAISS-индекс в памяти
def load_faiss(session: Session, discipline_id: int, scope_docs: list[int] | None = None):
    dim = 384 # размерность векторов
    index = faiss.IndexFlatIP(dim) # FAISS-индекс для поиска текстовых фрагментов
    meta  = []
    q = select(DocumentChunk).join(Document).where(Document.discipline_id == discipline_id)
    if scope_docs:
        q = q.where(DocumentChunk.document_id.in_(scope_docs))
    for ch in session.exec(q):
        vec = np.frombuffer(ch.embedding, dtype="float32")
        index.add(vec.reshape(1, -1))
        meta.append(ch)
    return index, meta


# Найти наиболее релевантные текстовые фрагменты для заданного вопроса.
def retrieve(question: str,
             session: Session,
             discipline_id: int,
             scope_docs: list[int] | None = None,
             scope_section: str    | None = None) -> str:
    # Собираем FAISS-индекс
    index, meta = load_faiss(session, discipline_id, scope_docs)

    # Формируем единый запрос: "[раздел] • [вопрос]"
    prefix = scope_section or ""
    if question:
        query = prefix + " • " + question
    else:
        query = prefix

    # Делаем эмбеддинг для полученного запроса
    q_emb = np.array(embed([query])[0], dtype="float32")

    D, I = index.search(np.array([q_emb]), k=4)
    
    # Склеиваем тексты четырёх самых релевантных чанков
    results: list[str] = []
    for idx in I[0][:4]:
        if idx < len(meta):
            results.append(meta[idx].text)

    # Возвращаем объединённый текст (max 4 чанка)
    return "\n\n".join(results)

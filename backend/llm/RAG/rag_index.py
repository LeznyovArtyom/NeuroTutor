from sqlmodel import Session, delete
from database.sql_models import Document, DocumentChunk
from llm.assistant_core import extract_text
from llm.RAG.rag_utils import split_into_chunks, embed
import numpy as np


# Стром индекс - чанки, эмбеддинги, сохранение в бд
def build_index(document: Document, session: Session):
    """Разбиваем документ, считаем эмбеддинги, сохраняем в БД / FAISS."""
    text = extract_text(document.data, document.name)
    chunks = split_into_chunks(text, size=400, overlap=40)   # Чанк по 400 символов, парекрытие 40 символов

    vectors = embed(chunks)  # это list[list[float]]
    for txt, vec in zip(chunks, vectors):
        # конвертим в numpy массив float32 и берём сырые байты
        arr = np.array(vec, dtype="float32")
        blob = arr.tobytes()
        session.add(DocumentChunk(
            document_id=document.id,
            text=txt,
            embedding=blob
        ))
    session.commit()


def delete_index_for_document(document_id: int, session: Session):
    """
    Удаляем из RAG-индекса все фрагменты (DocumentChunk) для документа.
    """
    session.exec(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
    session.commit()

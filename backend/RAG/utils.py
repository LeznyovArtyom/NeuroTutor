from sentence_transformers import SentenceTransformer

_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def embed(texts: list[str]) -> list[list[float]]:
    """Считает эмбеддинги для списка текстов."""
    return _MODEL.encode(texts, show_progress_bar=False).tolist()

def split_into_chunks(text: str, size=400, overlap=40) -> list[str]:
    """Разбивает текст на чанки по приблизительно `size` слов с перекрытием."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i : i + size])
        if len(chunk.split()) > 20:
            chunks.append(chunk)
    return chunks
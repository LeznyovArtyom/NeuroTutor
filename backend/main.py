from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, disciplines, works, students, chats


app = FastAPI(title="API NeuroTutor", description="API для цифрового помощника", version="1.0.0", docs_url="/docs", openapi_url="/openapi.json", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(disciplines.router)
app.include_router(works.router)
app.include_router(students.router)
app.include_router(chats.router)


# Получить чат в режиме Помощь

# Получить чат в режиме Сдача работы

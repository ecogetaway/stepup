from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Knowledge Copilot"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000"

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    CHROMA_PERSIST_DIR: Path = Path("./data/chroma_db")
    CHROMA_COLLECTION: str = "enterprise_docs"

    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_TOP_K: int = 5

    BM25_TOP_K: int = 20
    VECTOR_TOP_K: int = 20
    RRF_K: int = 60

    LLM_PROVIDER: str = "ollama"
    LLM_TIMEOUT_SECONDS: float = 25.0
    SKIP_LLM: bool = False
    USE_CROSS_ENCODER_RERANK: bool = False
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-2-9b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_HTTP_REFERER: str = "https://stepupcopilot.netlify.app"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    CONFIDENCE_ESCALATION_THRESHOLD: float = 0.60
    HALLUCINATION_SIMILARITY_THRESHOLD: float = 0.35

    DATA_DIR: Path = Path("./data")
    SOP_DIR: Path = Path("./data/sops")
    TICKET_CSV: Path = Path("./data/tickets/tickets.csv")
    IT_DOCS_DIR: Path = Path("./data/it_docs")

    class Config:
        env_file = ".env"

    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()

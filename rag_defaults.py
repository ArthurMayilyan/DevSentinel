from app_settings import get_app_settings


_SETTINGS = get_app_settings()


DEFAULT_RAG_TOP_K = (
    _SETTINGS.rag.top_k
)

DEFAULT_RAG_CHUNK_MAX_CHARS = (
    _SETTINGS.rag.chunk_max_chars
)

DEFAULT_RAG_CHUNK_OVERLAP_CHARS = (
    _SETTINGS.rag.chunk_overlap_chars
)

DEFAULT_RAG_AGENT_MAX_STEPS = (
    _SETTINGS.rag.agent_max_steps
)

DEFAULT_RAG_RETRIEVAL_STRATEGY = (
    _SETTINGS.rag.retrieval_strategy
)
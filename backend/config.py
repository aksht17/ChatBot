import os

from dotenv import load_dotenv

load_dotenv()

# ===== API KEYS =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# ===== DATA SOURCES =====
# Each source has a "type" plus its specific settings and an "enabled" flag.
# Supported types: "local_path", "website", "google_drive", "web_file".
DATA_SOURCES = [
    {
        # Swish company source files stored in backend/Swish.
        # Relative paths are resolved from ChatBot/backend.
        "type": "local_path",
        "enabled": True,
        "path": "Swish",
        # Set True to also download and ingest linked resumes/attachments.
        "follow_urls_in_text": True,
        # Swish local files are allowed to follow URLs found inside the text.
        "allow_external_web_crawl": True,
    },
    {
        "type": "website",
        "enabled": True,
        "url": "https://justswish.in",
        # Crawl the site a bit deeper so we capture linked pages.
        "depth": 3,
    },
    {
        "type": "google_drive",
        "enabled": False,
        "url": "https://drive.google.com/drive/folders/1EidATAo0bguciRNFQdzyfj9XWiEEYsl8",
    },
]

# ===== DEPRECATED DATA SOURCES (will be removed in a future version) =====
IITK_PLACEMENT_URL = "https://justswish.in"
STUDENT_EXCEL_PATH = ""
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1EidATAo0bguciRNFQdzyfj9XWiEEYsl8"

# ===== INGESTION SETTINGS =====
LINK_FOLLOW_DEPTH = 2
FOLLOW_URLS_IN_TEXT = True
# File sources can keep all URLs as text, but should not recursively crawl
# arbitrary external websites unless explicitly enabled.
FOLLOW_EXTERNAL_URLS_FROM_FILES = False
# Website pages can be capped to avoid crawling too many inline links.
WEBSITE_MAX_URLS_PER_DOC = 20
# Local files like PDFs/DOCX/CSV can include all detected links.
FILE_MAX_URLS_PER_DOC = None
ARCHIVE_DEPTH = 1
ENABLE_OCR = True
ENABLE_AUDIO_VIDEO = True
WHISPER_MODEL = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
CACHE_DIR = ".ingest_cache"
ENABLE_CACHE = True
FORCE_REBUILD_CHECKPOINTS = False
EMBED_BATCH_SIZE = 20
EMBED_REQUEST_DELAY_SECONDS = 2.0
CHUNK_TOKENS = 2000
CHUNK_OVERLAP_TOKENS = 20

# ===== MODEL =====
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIMENSION = 3072
LLM_MODEL = "llama-3.1-8b-instant"

# ===== RAG SETTINGS =====
RAG_TOP_K = 10
SYSTEM_PROMPT = "You are the official AI assistant for Swish. Your role is to provide accurate, concise, trustworthy, and professional answers ONLY using the information retrieved from the Swish knowledge base and official Swish documents. STRICT RULES: NEVER behave like a general-purpose AI assistant. NEVER make up information, policies, pricing, features, timelines, or technical details. NEVER answer from your own knowledge if the information is not present in retrieved context. If the retrieved context is insufficient, unclear, outdated, or unrelated: clearly say you could not find verified information politely. Ask the user to contact the official Swish support team and provide official Swish contact details only if they ask for it and provide their email id from databse.Keep answers SHORT and CUSTOMER-SUPPORT STYLE: Prefer 1-2 sentences Avoid long explanations unless user explicitly asks for detail Do not dump unnecessary information Prioritize: accuracy clarity trustworthiness concise responses Maintain a professional and confident tone like an official company support chatbot. If multiple retrieved documents conflict: say the information appears inconsistent recommend contacting official support for confirmation When answering: use only the retrieved context summarize instead of copying large text blocks avoid technical jargon unless necessary If the user asks unrelated/general questions outside Swish: politely state that you are designed only for Swish-related assistance."


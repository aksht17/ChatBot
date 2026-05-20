import os

from dotenv import load_dotenv

load_dotenv()

# ===== API KEYS =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "iitk-placements-3072")

# ===== DATA SOURCES =====
# Each source has a "type" plus its specific settings and an "enabled" flag.
# Supported types: "local_path", "website", "google_drive", "web_file".
DATA_SOURCES = [
    {
        # Ingest only data-25-26 for now.
        # Relative paths are resolved from ChatBot/backend.
        "type": "local_path",
        "enabled": True,
        "path": "data-25-26",
        # Set True to also download and ingest linked resumes/attachments.
        "follow_urls_in_text": False,
    },
    {
        "type": "website",
        "enabled": False,
        "url": "https://iitk-spo26.netlify.app",
    },
    {
        "type": "google_drive",
        "enabled": False,
        "url": "https://drive.google.com/drive/folders/1EidATAo0bguciRNFQdzyfj9XWiEEYsl8",
    },
]

# ===== DEPRECATED DATA SOURCES (will be removed in a future version) =====
IITK_PLACEMENT_URL = "https://iitk-spo26.netlify.app"
STUDENT_EXCEL_PATH = ""
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1EidATAo0bguciRNFQdzyfj9XWiEEYsl8"

# ===== INGESTION SETTINGS =====
LINK_FOLLOW_DEPTH = 2
FOLLOW_URLS_IN_TEXT = True
MAX_URLS_PER_DOC = 20
ARCHIVE_DEPTH = 1
ENABLE_OCR = True
ENABLE_AUDIO_VIDEO = True
WHISPER_MODEL = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
CACHE_DIR = ".ingest_cache"
ENABLE_CACHE = True
EMBED_BATCH_SIZE = 16
EMBED_REQUEST_DELAY_SECONDS = 1.0
CHUNK_TOKENS = 2000
CHUNK_OVERLAP_TOKENS = 20

# ===== MODEL =====
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIMENSION = 3072
LLM_MODEL = "llama-3.1-8b-instant"

# ===== RAG SETTINGS =====
RAG_TOP_K = 10
SYSTEM_PROMPT = "You are a helpful assistant/chatbot providing information about placement statistics and student data and keep it formal and interactive with emojis."


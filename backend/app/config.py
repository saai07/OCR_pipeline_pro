import json
import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    VLLM_BASE_URL: str
    VLLM_MODEL_NAME: str
    VLLM_API_KEY: Optional[str] = None
    VLLM_MAX_TOKENS: int = 4096
    VLLM_TEMPERATURE: float = 0.1
    PDF_DPI: int = 150
    PDF_MAX_PAGES: int = 10
    ALLOWED_TAGS: str = "BMR,COA,prescription,lab_report,discharge_summary,radiology_report"
    MAX_UPLOAD_SIZE_MB: int = 20
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    SYSTEM_PROMPTS_PATH: str = "app/system_prompts.json"
    CONCURRENCY_LIMIT: int = 1
    CHUNK_SIZE: int = 8
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_tags_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_TAGS.split(",") if t.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def load_system_prompts(self) -> Dict[str, str]:
        path = self.SYSTEM_PROMPTS_PATH
        
        # Resolve path dynamically to ensure it can be found from any CWD
        if not os.path.isabs(path):
            # Check relative to app directory (where config.py lives)
            config_dir = os.path.dirname(os.path.abspath(__file__))
            # app/system_prompts.json -> app/../app/system_prompts.json
            # system_prompts.json is in app/system_prompts.json, and config.py is in app/config.py
            # So if SYSTEM_PROMPTS_PATH is "app/system_prompts.json", the app folder is config_dir.
            # So if it starts with app/, let's resolve it relative to parent of app/
            parent_dir = os.path.dirname(config_dir)
            candidate = os.path.join(parent_dir, path)
            if os.path.exists(candidate):
                path = candidate
            elif os.path.exists(os.path.join(config_dir, os.path.basename(path))):
                path = os.path.join(config_dir, os.path.basename(path))
            elif os.path.exists(path):
                pass
            else:
                # CWD check
                cwd_candidate = os.path.join(os.getcwd(), path)
                if os.path.exists(cwd_candidate):
                    path = cwd_candidate

        if not os.path.exists(path):
            raise FileNotFoundError(
                f"System prompts configuration file not found. Tried paths, but file is missing at: {path}. "
                f"Please ensure SYSTEM_PROMPTS_PATH is set correctly."
            )

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Ensure all allowed tags have a prompt in the json file
        for tag in self.allowed_tags_list:
            if tag not in data:
                # Create a generic fallback prompt for undefined tags
                data[tag] = (
                    f"You are an expert document OCR engine. Perform OCR on this {tag} document. "
                    "Extract all text, data, tables, and structures accurately and represent them in markdown."
                )
        return data

# Initialize settings
# Note: In production/testing, if .env doesn't exist yet, we catch the validation error 
# or let it propagate to warn about missing required env variables.
settings = Settings()

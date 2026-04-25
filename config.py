import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "WordVivid"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    PORT: int = int(os.getenv("PORT", 3243))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    IMAGES_DIR: Path = DATA_DIR / "images"
    AUDIO_DIR: Path = DATA_DIR / "audio"
    CARDS_DIR: Path = DATA_DIR / "cards"
    GALLERY_DIR: Path = DATA_DIR / "gallery"
    
    VOLCENGINE_API_KEY: Optional[str] = os.getenv("VOLCENGINE_API_KEY")
    VOLCENGINE_CHAT_MODEL: str = os.getenv("VOLCENGINE_CHAT_MODEL", "doubao-seed-1.8")
    VOLCENGINE_IMAGE_MODEL: str = os.getenv("VOLCENGINE_IMAGE_MODEL", "doubao-seedream-5.0-lite")
    VOLCENGINE_TTS_APPID: Optional[str] = os.getenv("VOLCENGINE_TTS_APPID")
    VOLCENGINE_TTS_ACCESS_TOKEN: Optional[str] = os.getenv("VOLCENGINE_TTS_ACCESS_TOKEN")
    
    VOLCENGINE_CHAT_URL: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    VOLCENGINE_IMAGE_URL: str = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    VOLCENGINE_TTS_URL: str = "https://openspeech.bytedance.com/api/v1/tts"
    
    IMAGE_SIZE: str = "2048x2048"
    IMAGE_QUALITY: str = "standard"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


IMAGE_STYLES: Dict[str, Dict[str, Any]] = {
    "cartoon": {
        "description": "卡通风格 - 适合儿童青少年，色彩鲜艳",
        "prompt_prefix": "可爱的卡通风格，色彩鲜艳明亮，适合儿童青少年，",
        "suffix": ", 4K高清，细节丰富，适合记忆卡片"
    },
    "anime": {
        "description": "动漫风格 - 日系动漫风格",
        "prompt_prefix": "日系动漫风格，精美画风，",
        "suffix": ", 动漫插画风格，高分辨率"
    },
    "realistic": {
        "description": "写实风格 - 照片级真实感",
        "prompt_prefix": "写实摄影风格，照片级真实感，",
        "suffix": ", 专业摄影，高清晰度，真实感强"
    },
    "watercolor": {
        "description": "水彩风格 - 艺术水彩效果",
        "prompt_prefix": "水彩画风格，柔和的色彩过渡，艺术感强，",
        "suffix": ", 水彩插画，手绘风格，艺术感"
    },
    "pixel": {
        "description": "像素风格 - 复古游戏风格",
        "prompt_prefix": "像素艺术风格，复古游戏风格，8-bit风格，",
        "suffix": ", 像素风，复古游戏美术"
    },
    "3d": {
        "description": "3D风格 - 三维渲染效果",
        "prompt_prefix": "3D渲染风格，三维效果，Blender风格，",
        "suffix": ", 3D建模渲染，高质量3D效果"
    }
}


VOICE_TYPES: Dict[str, str] = {
    "zh_female_shuangkuaisisi_moon_bigtts": "女声 - 活泼甜美",
    "zh_male_chunhou_chaoren_bigtts": "男声 - 沉稳磁性",
    "zh_female_wanrou_lingwei_bigtts": "女声 - 温柔亲切",
    "zh_male_novel_yechen_bigtts": "男声 - 故事讲述",
    "zh_female_child_xiaoyue_bigtts": "童声 - 小女孩",
    "zh_male_child_doubao_bigtts": "童声 - 小男孩"
}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def ensure_directories():
    settings = get_settings()
    for directory in [
        settings.DATA_DIR,
        settings.IMAGES_DIR,
        settings.AUDIO_DIR,
        settings.CARDS_DIR,
        settings.GALLERY_DIR
    ]:
        directory.mkdir(parents=True, exist_ok=True)

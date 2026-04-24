import json
import base64
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from config import get_settings, IMAGE_STYLES, VOICE_TYPES
from services.volcengine_service import VolcEngineService


class CardStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CardImage:
    url: str
    style: str
    prompt: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CardAudio:
    url: str
    voice_type: str
    duration: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CardMetadata:
    category: str = "default"
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    review_count: int = 0
    correct_count: int = 0
    last_reviewed_at: Optional[str] = None


@dataclass
class MemoryCard:
    card_id: str
    user_id: str
    text: str
    original_text: str
    segment_index: int = 0
    image: Optional[CardImage] = None
    audio: Optional[CardAudio] = None
    metadata: CardMetadata = field(default_factory=CardMetadata)
    status: str = CardStatus.DRAFT.value

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.image:
            data["image"] = asdict(self.image)
        if self.audio:
            data["audio"] = asdict(self.audio)
        if self.metadata:
            data["metadata"] = asdict(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryCard":
        image_data = data.get("image")
        audio_data = data.get("audio")
        metadata_data = data.get("metadata", {})
        
        return cls(
            card_id=data["card_id"],
            user_id=data["user_id"],
            text=data["text"],
            original_text=data.get("original_text", data["text"]),
            segment_index=data.get("segment_index", 0),
            image=CardImage(**image_data) if image_data else None,
            audio=CardAudio(**audio_data) if audio_data else None,
            metadata=CardMetadata(**metadata_data) if metadata_data else CardMetadata(),
            status=data.get("status", CardStatus.DRAFT.value)
        )


class CardGeneratorService:
    def __init__(self, volcengine_service: Optional[VolcEngineService] = None):
        self.settings = get_settings()
        self.volcengine = volcengine_service or VolcEngineService()

    def _generate_card_id(self) -> str:
        return f"card_{uuid.uuid4().hex[:12]}"

    def _save_base64_image(self, card_id: str, base64_data: str) -> str:
        image_bytes = base64.b64decode(base64_data)
        image_path = self.settings.IMAGES_DIR / f"{card_id}.png"
        image_path.write_bytes(image_bytes)
        return f"/data/images/{card_id}.png"

    def _save_audio(self, card_id: str, audio_data: bytes) -> str:
        audio_path = self.settings.AUDIO_DIR / f"{card_id}.mp3"
        audio_path.write_bytes(audio_data)
        return f"/data/audio/{card_id}.mp3"

    def _save_card_json(self, card: MemoryCard):
        user_dir = self.settings.CARDS_DIR / card.user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        card_path = user_dir / f"{card.card_id}.json"
        card_path.write_text(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))

    def generate_card(
        self,
        user_id: str,
        text: str,
        original_text: str = "",
        segment_index: int = 0,
        style: str = "cartoon",
        voice_type: str = "zh_female_shuangkuaisisi_moon_bigtts",
        generate_image: bool = True,
        generate_audio: bool = True,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        image_model: Optional[str] = None
    ) -> Dict[str, Any]:
        if api_key:
            self.volcengine = VolcEngineService(
                api_key=api_key,
                chat_model=chat_model,
                image_model=image_model
            )

        card_id = self._generate_card_id()
        
        card = MemoryCard(
            card_id=card_id,
            user_id=user_id,
            text=text,
            original_text=original_text or text,
            segment_index=segment_index,
            status=CardStatus.GENERATING.value
        )

        try:
            if generate_image:
                self._generate_card_image(card, text, style)

            if generate_audio:
                self._generate_card_audio(card, text, voice_type)

            card.status = CardStatus.COMPLETED.value
            card.metadata.updated_at = datetime.now().isoformat()
            
            self._save_card_json(card)

            return {
                "success": True,
                "data": {
                    "card_id": card.card_id,
                    "text": card.text,
                    "image_url": card.image.url if card.image else None,
                    "audio_url": card.audio.url if card.audio else None,
                    "style": style,
                    "voice_type": voice_type,
                    "created_at": card.metadata.created_at
                }
            }

        except Exception as e:
            card.status = CardStatus.FAILED.value
            self._save_card_json(card)
            return {
                "success": False,
                "error": f"卡片生成失败: {str(e)}"
            }

    def _generate_card_image(self, card: MemoryCard, text: str, style: str):
        image_prompt = self.volcengine.generate_image_prompt(text, style)
        
        image_result = self.volcengine.generate_image(image_prompt)
        
        if image_result.success and image_result.image_base64:
            image_url = self._save_base64_image(card.card_id, image_result.image_base64)
            
            card.image = CardImage(
                url=image_url,
                style=style,
                prompt=image_result.revised_prompt or image_prompt
            )
        else:
            raise Exception(f"图像生成失败: {image_result.error}")

    def _generate_card_audio(self, card: MemoryCard, text: str, voice_type: str):
        tts_result = self.volcengine.generate_tts(text, voice_type)
        
        if tts_result.success and tts_result.audio_data:
            audio_url = self._save_audio(card.card_id, tts_result.audio_data)
            
            card.audio = CardAudio(
                url=audio_url,
                voice_type=voice_type,
                duration=tts_result.duration or 0.0
            )
        else:
            raise Exception(f"语音生成失败: {tts_result.error}")

    def generate_cards_batch(
        self,
        user_id: str,
        segments: List[Dict[str, Any]],
        original_text: str = "",
        style: str = "cartoon",
        voice_type: str = "zh_female_shuangkuaisisi_moon_bigtts",
        generate_image: bool = True,
        generate_audio: bool = True,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        image_model: Optional[str] = None
    ) -> Dict[str, Any]:
        results = []
        errors = []

        for segment in segments:
            result = self.generate_card(
                user_id=user_id,
                text=segment["text"],
                original_text=original_text,
                segment_index=segment["index"],
                style=style,
                voice_type=voice_type,
                generate_image=generate_image,
                generate_audio=generate_audio,
                api_key=api_key,
                chat_model=chat_model,
                image_model=image_model
            )
            
            if result["success"]:
                results.append(result["data"])
            else:
                errors.append({
                    "segment_index": segment["index"],
                    "text": segment["text"],
                    "error": result["error"]
                })

        return {
            "success": len(results) > 0,
            "data": {
                "cards": results,
                "total_count": len(segments),
                "success_count": len(results),
                "failed_count": len(errors)
            },
            "errors": errors if errors else None
        }

    def load_card(self, card_id: str, user_id: str) -> Optional[MemoryCard]:
        card_path = self.settings.CARDS_DIR / user_id / f"{card_id}.json"
        if card_path.exists():
            data = json.loads(card_path.read_text())
            return MemoryCard.from_dict(data)
        return None

    def update_card_metadata(self, card_id: str, user_id: str, updates: Dict[str, Any]) -> bool:
        card = self.load_card(card_id, user_id)
        if not card:
            return False
        
        if "category" in updates:
            card.metadata.category = updates["category"]
        if "tags" in updates:
            card.metadata.tags = updates["tags"]
        
        card.metadata.updated_at = datetime.now().isoformat()
        self._save_card_json(card)
        return True

    def record_review(self, card_id: str, user_id: str, is_correct: bool) -> bool:
        card = self.load_card(card_id, user_id)
        if not card:
            return False
        
        card.metadata.review_count += 1
        if is_correct:
            card.metadata.correct_count += 1
        card.metadata.last_reviewed_at = datetime.now().isoformat()
        card.metadata.updated_at = datetime.now().isoformat()
        
        self._save_card_json(card)
        return True

import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


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


@dataclass
class User:
    user_id: str
    username: str
    email: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data.get("email"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_login_at=data.get("last_login_at")
        )

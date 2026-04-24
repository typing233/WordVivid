import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from config import get_settings
from models.card import MemoryCard


class Category(str, Enum):
    DEFAULT = "default"
    POETRY = "古诗词"
    ENGLISH = "英语"
    MATH = "数学公式"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    SCIENCE = "科学"
    OTHER = "其他"


@dataclass
class LibraryStats:
    total_cards: int = 0
    total_reviews: int = 0
    average_correct_rate: float = 0.0
    categories_count: Dict[str, int] = field(default_factory=dict)


class MemoryLibraryService:
    def __init__(self):
        self.settings = get_settings()

    def _get_user_library_path(self, user_id: str) -> Path:
        return self.settings.CARDS_DIR / user_id

    def list_cards(
        self,
        user_id: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        user_path = self._get_user_library_path(user_id)
        
        if not user_path.exists():
            return {
                "success": True,
                "data": {
                    "cards": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0
                }
            }

        cards = []
        for card_file in user_path.glob("card_*.json"):
            try:
                data = json.loads(card_file.read_text())
                card = MemoryCard.from_dict(data)
                
                if category and card.metadata.category != category:
                    continue
                
                if tags:
                    card_tags = set(card.metadata.tags)
                    if not any(tag in card_tags for tag in tags):
                        continue
                
                cards.append(card)
            except Exception:
                continue

        reverse = sort_order == "desc"
        if sort_by == "created_at":
            cards.sort(key=lambda x: x.metadata.created_at, reverse=reverse)
        elif sort_by == "review_count":
            cards.sort(key=lambda x: x.metadata.review_count, reverse=reverse)
        elif sort_by == "correct_rate":
            cards.sort(
                key=lambda x: (x.metadata.correct_count / max(x.metadata.review_count, 1)),
                reverse=reverse
            )

        total = len(cards)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_cards = cards[start:end]

        return {
            "success": True,
            "data": {
                "cards": [self._card_to_response(card) for card in paginated_cards],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }

    def get_card(self, user_id: str, card_id: str) -> Optional[Dict[str, Any]]:
        card_path = self._get_user_library_path(user_id) / f"{card_id}.json"
        
        if not card_path.exists():
            return None
        
        try:
            data = json.loads(card_path.read_text())
            card = MemoryCard.from_dict(data)
            return self._card_to_response(card)
        except Exception:
            return None

    def _card_to_response(self, card: MemoryCard) -> Dict[str, Any]:
        correct_rate = 0.0
        if card.metadata.review_count > 0:
            correct_rate = card.metadata.correct_count / card.metadata.review_count

        return {
            "card_id": card.card_id,
            "text": card.text,
            "original_text": card.original_text,
            "segment_index": card.segment_index,
            "image_url": card.image.url if card.image else None,
            "image_style": card.image.style if card.image else None,
            "audio_url": card.audio.url if card.audio else None,
            "audio_voice_type": card.audio.voice_type if card.audio else None,
            "audio_duration": card.audio.duration if card.audio else 0.0,
            "category": card.metadata.category,
            "tags": card.metadata.tags,
            "created_at": card.metadata.created_at,
            "updated_at": card.metadata.updated_at,
            "review_count": card.metadata.review_count,
            "correct_count": card.metadata.correct_count,
            "correct_rate": round(correct_rate, 2),
            "last_reviewed_at": card.metadata.last_reviewed_at,
            "status": card.status
        }

    def update_card(
        self,
        user_id: str,
        card_id: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        card_path = self._get_user_library_path(user_id) / f"{card_id}.json"
        
        if not card_path.exists():
            return {
                "success": False,
                "error": "卡片不存在"
            }

        try:
            data = json.loads(card_path.read_text())
            card = MemoryCard.from_dict(data)

            if category:
                card.metadata.category = category
            if tags is not None:
                card.metadata.tags = tags
            
            card.metadata.updated_at = datetime.now().isoformat()

            card_path.write_text(json.dumps(card.to_dict(), ensure_ascii=False, indent=2))

            return {
                "success": True,
                "data": self._card_to_response(card)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"更新卡片失败: {str(e)}"
            }

    def delete_card(self, user_id: str, card_id: str) -> Dict[str, Any]:
        card_path = self._get_user_library_path(user_id) / f"{card_id}.json"
        image_path = self.settings.IMAGES_DIR / f"{card_id}.png"
        audio_path = self.settings.AUDIO_DIR / f"{card_id}.mp3"

        if not card_path.exists():
            return {
                "success": False,
                "error": "卡片不存在"
            }

        try:
            card_path.unlink()
            
            if image_path.exists():
                image_path.unlink()
            
            if audio_path.exists():
                audio_path.unlink()

            return {
                "success": True,
                "message": "卡片已删除"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除卡片失败: {str(e)}"
            }

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        user_path = self._get_user_library_path(user_id)
        
        if not user_path.exists():
            return {
                "success": True,
                "data": {
                    "total_cards": 0,
                    "total_reviews": 0,
                    "average_correct_rate": 0.0,
                    "categories_count": {}
                }
            }

        total_cards = 0
        total_reviews = 0
        total_correct = 0
        categories_count: Dict[str, int] = {}

        for card_file in user_path.glob("card_*.json"):
            try:
                data = json.loads(card_file.read_text())
                card = MemoryCard.from_dict(data)
                
                total_cards += 1
                total_reviews += card.metadata.review_count
                total_correct += card.metadata.correct_count
                
                category = card.metadata.category or "default"
                categories_count[category] = categories_count.get(category, 0) + 1
            except Exception:
                continue

        average_correct_rate = 0.0
        if total_reviews > 0:
            average_correct_rate = total_correct / total_reviews

        return {
            "success": True,
            "data": {
                "total_cards": total_cards,
                "total_reviews": total_reviews,
                "average_correct_rate": round(average_correct_rate, 2),
                "categories_count": categories_count
            }
        }

    def get_categories(self, user_id: str) -> Dict[str, Any]:
        user_path = self._get_user_library_path(user_id)
        
        if not user_path.exists():
            return {
                "success": True,
                "data": {
                    "categories": []
                }
            }

        categories: Dict[str, int] = {}

        for card_file in user_path.glob("card_*.json"):
            try:
                data = json.loads(card_file.read_text())
                card = MemoryCard.from_dict(data)
                
                category = card.metadata.category or "default"
                categories[category] = categories.get(category, 0) + 1
            except Exception:
                continue

        category_list = [
            {"name": name, "count": count}
            for name, count in categories.items()
        ]

        return {
            "success": True,
            "data": {
                "categories": category_list
            }
        }

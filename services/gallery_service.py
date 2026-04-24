import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from config import get_settings
from models.card import MemoryCard


class GallerySort(str, Enum):
    HOT = "hot"
    NEW = "new"
    POPULAR = "popular"


@dataclass
class GalleryCard:
    gallery_id: str
    card_id: str
    user_id: str
    title: str
    description: str
    text: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    style: str = "cartoon"
    category: str = "default"
    tags: List[str] = field(default_factory=list)
    likes: int = 0
    views: int = 0
    shared_at: str = field(default_factory=lambda: datetime.now().isoformat())
    hot_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GalleryCard":
        return cls(
            gallery_id=data["gallery_id"],
            card_id=data["card_id"],
            user_id=data["user_id"],
            title=data["title"],
            description=data["description"],
            text=data["text"],
            image_url=data.get("image_url"),
            audio_url=data.get("audio_url"),
            style=data.get("style", "cartoon"),
            category=data.get("category", "default"),
            tags=data.get("tags", []),
            likes=data.get("likes", 0),
            views=data.get("views", 0),
            shared_at=data.get("shared_at", datetime.now().isoformat()),
            hot_score=data.get("hot_score", 0.0)
        )


class GalleryService:
    def __init__(self):
        self.settings = get_settings()
        self._gallery_file = self.settings.GALLERY_DIR / "shared_cards.json"
        self._ensure_gallery_file()

    def _ensure_gallery_file(self):
        self.settings.GALLERY_DIR.mkdir(parents=True, exist_ok=True)
        if not self._gallery_file.exists():
            self._gallery_file.write_text(json.dumps([], ensure_ascii=False, indent=2))

    def _load_gallery(self) -> List[GalleryCard]:
        try:
            data = json.loads(self._gallery_file.read_text())
            return [GalleryCard.from_dict(item) for item in data]
        except Exception:
            return []

    def _save_gallery(self, cards: List[GalleryCard]):
        data = [card.to_dict() for card in cards]
        self._gallery_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _generate_gallery_id(self) -> str:
        return f"gallery_{uuid.uuid4().hex[:12]}"

    def _calculate_hot_score(self, card: GalleryCard) -> float:
        try:
            shared_time = datetime.fromisoformat(card.shared_at)
            age_hours = (datetime.now() - shared_time).total_seconds() / 3600
            
            likes_weight = 2.0
            views_weight = 0.1
            age_weight = -0.1
            
            score = (
                card.likes * likes_weight +
                card.views * views_weight +
                age_hours * age_weight
            )
            
            return max(0.0, score)
        except Exception:
            return 0.0

    def share_card(
        self,
        user_id: str,
        card_id: str,
        title: str,
        description: str,
        category: str = "default",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        user_card_path = self.settings.CARDS_DIR / user_id / f"{card_id}.json"
        
        if not user_card_path.exists():
            return {
                "success": False,
                "error": "卡片不存在"
            }

        try:
            card_data = json.loads(user_card_path.read_text())
            card = MemoryCard.from_dict(card_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"读取卡片失败: {str(e)}"
            }

        gallery = self._load_gallery()
        
        for existing in gallery:
            if existing.card_id == card_id and existing.user_id == user_id:
                return {
                    "success": False,
                    "error": "该卡片已分享到画廊"
                }

        gallery_id = self._generate_gallery_id()
        
        gallery_card = GalleryCard(
            gallery_id=gallery_id,
            card_id=card_id,
            user_id=user_id,
            title=title,
            description=description,
            text=card.text,
            image_url=card.image.url if card.image else None,
            audio_url=card.audio.url if card.audio else None,
            style=card.image.style if card.image else "cartoon",
            category=category,
            tags=tags or []
        )

        gallery.append(gallery_card)
        self._save_gallery(gallery)

        return {
            "success": True,
            "data": {
                "gallery_id": gallery_id,
                "title": title,
                "shared_at": gallery_card.shared_at
            }
        }

    def list_gallery(
        self,
        sort: str = GallerySort.NEW.value,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        gallery = self._load_gallery()

        if category:
            gallery = [card for card in gallery if card.category == category]

        if search_query:
            query = search_query.lower()
            gallery = [
                card for card in gallery
                if query in card.title.lower() or
                   query in card.description.lower() or
                   query in card.text.lower() or
                   any(query in tag.lower() for tag in card.tags)
            ]

        for card in gallery:
            card.hot_score = self._calculate_hot_score(card)

        if sort == GallerySort.HOT.value:
            gallery.sort(key=lambda x: x.hot_score, reverse=True)
        elif sort == GallerySort.POPULAR.value:
            gallery.sort(key=lambda x: (x.likes, x.views), reverse=True)
        else:
            gallery.sort(key=lambda x: x.shared_at, reverse=True)

        total = len(gallery)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_cards = gallery[start:end]

        return {
            "success": True,
            "data": {
                "cards": [self._gallery_card_to_response(card) for card in paginated_cards],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "sort": sort
            }
        }

    def _gallery_card_to_response(self, card: GalleryCard) -> Dict[str, Any]:
        return {
            "gallery_id": card.gallery_id,
            "card_id": card.card_id,
            "user_id": card.user_id,
            "title": card.title,
            "description": card.description,
            "text": card.text,
            "image_url": card.image_url,
            "audio_url": card.audio_url,
            "style": card.style,
            "category": card.category,
            "tags": card.tags,
            "likes": card.likes,
            "views": card.views,
            "shared_at": card.shared_at,
            "hot_score": round(card.hot_score, 2)
        }

    def get_gallery_card(self, gallery_id: str, increment_view: bool = True) -> Dict[str, Any]:
        gallery = self._load_gallery()
        
        for card in gallery:
            if card.gallery_id == gallery_id:
                if increment_view:
                    card.views += 1
                    card.hot_score = self._calculate_hot_score(card)
                    self._save_gallery(gallery)
                
                return {
                    "success": True,
                    "data": self._gallery_card_to_response(card)
                }

        return {
            "success": False,
            "error": "画廊卡片不存在"
        }

    def like_card(self, gallery_id: str) -> Dict[str, Any]:
        gallery = self._load_gallery()
        
        for card in gallery:
            if card.gallery_id == gallery_id:
                card.likes += 1
                card.hot_score = self._calculate_hot_score(card)
                self._save_gallery(gallery)
                
                return {
                    "success": True,
                    "data": {
                        "gallery_id": gallery_id,
                        "likes": card.likes
                    }
                }

        return {
            "success": False,
            "error": "画廊卡片不存在"
        }

    def unshare_card(self, user_id: str, gallery_id: str) -> Dict[str, Any]:
        gallery = self._load_gallery()
        
        for i, card in enumerate(gallery):
            if card.gallery_id == gallery_id and card.user_id == user_id:
                gallery.pop(i)
                self._save_gallery(gallery)
                
                return {
                    "success": True,
                    "message": "卡片已从画廊移除"
                }

        return {
            "success": False,
            "error": "画廊卡片不存在或无权操作"
        }

    def get_categories(self) -> Dict[str, Any]:
        gallery = self._load_gallery()
        
        categories: Dict[str, int] = {}
        
        for card in gallery:
            category = card.category or "default"
            categories[category] = categories.get(category, 0) + 1

        category_list = [
            {"name": name, "count": count}
            for name, count in categories.items()
        ]
        category_list.sort(key=lambda x: x["count"], reverse=True)

        return {
            "success": True,
            "data": {
                "categories": category_list
            }
        }

    def get_popular_tags(self, limit: int = 20) -> Dict[str, Any]:
        gallery = self._load_gallery()
        
        tag_counts: Dict[str, int] = {}
        
        for card in gallery:
            for tag in card.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        popular_tags = [
            {"tag": tag, "count": count}
            for tag, count in tag_counts.items()
        ]
        popular_tags.sort(key=lambda x: x["count"], reverse=True)
        popular_tags = popular_tags[:limit]

        return {
            "success": True,
            "data": {
                "popular_tags": popular_tags
            }
        }

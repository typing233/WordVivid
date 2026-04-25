import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from config import get_settings
from models.storyline import Storyline, StorylineCard


class StorylineService:
    def __init__(self):
        self.settings = get_settings()
        self.storylines_dir = self.settings.DATA_DIR / "storylines"
        self.storylines_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_storylines_path(self, user_id: str) -> Path:
        user_path = self.storylines_dir / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def create_storyline(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        text: Optional[str] = None,
        split_mode: str = "paragraph",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        storyline_id = f"sl_{uuid.uuid4().hex[:8]}"
        
        storyline = Storyline(
            storyline_id=storyline_id,
            user_id=user_id,
            title=title,
            description=description,
            tags=tags or []
        )

        if text:
            cards = self._split_text_to_cards(text, split_mode)
            storyline.cards = cards
            storyline.sort_cards_by_index()

        self._save_storyline(storyline)

        return {
            "success": True,
            "data": self._storyline_to_response(storyline)
        }

    def _split_text_to_cards(self, text: str, split_mode: str) -> List[StorylineCard]:
        cards = []
        
        if split_mode == "paragraph":
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for i, para in enumerate(paragraphs):
                if para.strip():
                    cards.append(StorylineCard(
                        card_id=f"card_{uuid.uuid4().hex[:8]}",
                        text=para,
                        index=i
                    ))
        elif split_mode == "sentence":
            import re
            sentence_endings = r'[。！？.!?]+'
            sentences = re.split(f'({sentence_endings})', text)
            
            index = 0
            for i in range(0, len(sentences), 2):
                part = sentences[i]
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                full_sentence = f"{part}{punctuation}".strip()
                if full_sentence:
                    cards.append(StorylineCard(
                        card_id=f"card_{uuid.uuid4().hex[:8]}",
                        text=full_sentence,
                        index=index
                    ))
                    index += 1
        else:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            for i, line in enumerate(lines):
                if line.strip():
                    cards.append(StorylineCard(
                        card_id=f"card_{uuid.uuid4().hex[:8]}",
                        text=line,
                        index=i
                    ))

        return cards

    def get_storyline(self, user_id: str, storyline_id: str) -> Optional[Dict[str, Any]]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return None
        return {
            "success": True,
            "data": self._storyline_to_response(storyline)
        }

    def list_storylines(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        user_path = self._get_user_storylines_path(user_id)
        
        storylines = []
        for sl_file in user_path.glob("sl_*.json"):
            try:
                data = json.loads(sl_file.read_text())
                storyline = Storyline.from_dict(data)
                storylines.append(storyline)
            except Exception:
                continue

        storylines.sort(key=lambda sl: sl.updated_at, reverse=True)

        total = len(storylines)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated = storylines[start:end]

        return {
            "success": True,
            "data": {
                "storylines": [self._storyline_to_response(sl, include_cards=False) for sl in paginated],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }

    def update_card_order(
        self,
        user_id: str,
        storyline_id: str,
        new_order: List[str]
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        if storyline.update_card_order(new_order):
            self._save_storyline(storyline)
            return {
                "success": True,
                "data": self._storyline_to_response(storyline)
            }
        else:
            return {
                "success": False,
                "error": "卡片顺序更新失败"
            }

    def merge_cards(
        self,
        user_id: str,
        storyline_id: str,
        card_ids: List[str],
        new_text: str
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        merged_card = storyline.merge_cards(card_ids, new_text)
        if merged_card:
            self._save_storyline(storyline)
            return {
                "success": True,
                "data": {
                    "merged_card": merged_card.to_dict(),
                    "storyline": self._storyline_to_response(storyline)
                }
            }
        else:
            return {
                "success": False,
                "error": "卡片合并失败"
            }

    def split_card(
        self,
        user_id: str,
        storyline_id: str,
        card_id: str,
        split_index: int,
        part1_text: str,
        part2_text: str
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        new_cards = storyline.split_card(card_id, split_index, part1_text, part2_text)
        if new_cards:
            self._save_storyline(storyline)
            return {
                "success": True,
                "data": {
                    "new_cards": [card.to_dict() for card in new_cards],
                    "storyline": self._storyline_to_response(storyline)
                }
            }
        else:
            return {
                "success": False,
                "error": "卡片拆分失败"
            }

    def update_card_tags(
        self,
        user_id: str,
        storyline_id: str,
        card_id: str,
        tags: List[str],
        action: str = "set"
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        card_map = {card.card_id: card for card in storyline.cards}
        card = card_map.get(card_id)
        
        if not card:
            return {
                "success": False,
                "error": "卡片不存在"
            }

        if action == "add":
            for tag in tags:
                if tag not in card.tags:
                    card.tags.append(tag)
        elif action == "remove":
            for tag in tags:
                if tag in card.tags:
                    card.tags.remove(tag)
        else:
            card.tags = tags

        card.updated_at = datetime.now().isoformat()
        storyline.updated_at = datetime.now().isoformat()
        
        self._save_storyline(storyline)
        
        return {
            "success": True,
            "data": {
                "card": card.to_dict(),
                "storyline": self._storyline_to_response(storyline)
            }
        }

    def update_card_text(
        self,
        user_id: str,
        storyline_id: str,
        card_id: str,
        new_text: str
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        card_map = {card.card_id: card for card in storyline.cards}
        card = card_map.get(card_id)
        
        if not card:
            return {
                "success": False,
                "error": "卡片不存在"
            }

        card.text = new_text
        card.updated_at = datetime.now().isoformat()
        storyline.updated_at = datetime.now().isoformat()
        
        self._save_storyline(storyline)
        
        return {
            "success": True,
            "data": {
                "card": card.to_dict(),
                "storyline": self._storyline_to_response(storyline)
            }
        }

    def add_card(
        self,
        user_id: str,
        storyline_id: str,
        text: str,
        insert_after: Optional[str] = None
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        new_index = len(storyline.cards)
        if insert_after:
            card_map = {card.card_id: card for card in storyline.cards}
            ref_card = card_map.get(insert_after)
            if ref_card:
                new_index = ref_card.index + 1
                for card in storyline.cards:
                    if card.index >= new_index:
                        card.index += 1

        new_card = StorylineCard(
            card_id=f"card_{uuid.uuid4().hex[:8]}",
            text=text,
            index=new_index
        )

        storyline.cards.append(new_card)
        storyline.sort_cards_by_index()
        storyline.updated_at = datetime.now().isoformat()
        
        self._save_storyline(storyline)
        
        return {
            "success": True,
            "data": {
                "card": new_card.to_dict(),
                "storyline": self._storyline_to_response(storyline)
            }
        }

    def delete_card(
        self,
        user_id: str,
        storyline_id: str,
        card_id: str
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        card_map = {card.card_id: card for card in storyline.cards}
        card = card_map.get(card_id)
        
        if not card:
            return {
                "success": False,
                "error": "卡片不存在"
            }

        card_index = card.index
        storyline.cards.remove(card)

        for remaining_card in storyline.cards:
            if remaining_card.index > card_index:
                remaining_card.index -= 1

        storyline.sort_cards_by_index()
        storyline.updated_at = datetime.now().isoformat()
        
        self._save_storyline(storyline)
        
        return {
            "success": True,
            "data": self._storyline_to_response(storyline)
        }

    def delete_storyline(
        self,
        user_id: str,
        storyline_id: str
    ) -> Dict[str, Any]:
        user_path = self._get_user_storylines_path(user_id)
        sl_file = user_path / f"{storyline_id}.json"
        
        if not sl_file.exists():
            return {
                "success": False,
                "error": "故事线不存在"
            }

        try:
            sl_file.unlink()
            return {
                "success": True,
                "message": "故事线已删除"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除故事线失败: {str(e)}"
            }

    def update_storyline(
        self,
        user_id: str,
        storyline_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        storyline = self._load_storyline(user_id, storyline_id)
        if not storyline:
            return {
                "success": False,
                "error": "故事线不存在"
            }

        if title:
            storyline.title = title
        if description is not None:
            storyline.description = description
        if tags is not None:
            storyline.tags = tags

        storyline.updated_at = datetime.now().isoformat()
        self._save_storyline(storyline)

        return {
            "success": True,
            "data": self._storyline_to_response(storyline)
        }

    def _load_storyline(self, user_id: str, storyline_id: str) -> Optional[Storyline]:
        user_path = self._get_user_storylines_path(user_id)
        sl_file = user_path / f"{storyline_id}.json"
        
        if not sl_file.exists():
            return None

        try:
            data = json.loads(sl_file.read_text())
            return Storyline.from_dict(data)
        except Exception:
            return None

    def _save_storyline(self, storyline: Storyline):
        user_path = self._get_user_storylines_path(storyline.user_id)
        sl_file = user_path / f"{storyline.storyline_id}.json"
        
        with open(sl_file, 'w', encoding='utf-8') as f:
            json.dump(storyline.to_dict(), f, ensure_ascii=False, indent=2)

    def _storyline_to_response(self, storyline: Storyline, include_cards: bool = True) -> Dict[str, Any]:
        response = {
            "storyline_id": storyline.storyline_id,
            "title": storyline.title,
            "description": storyline.description,
            "tags": storyline.tags,
            "card_count": len(storyline.cards),
            "created_at": storyline.created_at,
            "updated_at": storyline.updated_at
        }

        if include_cards:
            response["cards"] = [card.to_dict() for card in storyline.cards]

        return response

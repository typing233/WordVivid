import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field


@dataclass
class StorylineCard:
    card_id: str
    text: str
    index: int
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorylineCard":
        return cls(
            card_id=data["card_id"],
            text=data["text"],
            index=data["index"],
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


@dataclass
class Storyline:
    storyline_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    cards: List[StorylineCard] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["cards"] = [card.to_dict() for card in self.cards]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Storyline":
        cards_data = data.get("cards", [])
        cards = [StorylineCard.from_dict(card) for card in cards_data]
        
        return cls(
            storyline_id=data["storyline_id"],
            user_id=data["user_id"],
            title=data["title"],
            description=data.get("description"),
            cards=cards,
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )

    def sort_cards_by_index(self):
        self.cards.sort(key=lambda c: c.index)

    def update_card_order(self, new_order: List[str]) -> bool:
        card_map = {card.card_id: card for card in self.cards}
        valid_order = [cid for cid in new_order if cid in card_map]
        
        if len(valid_order) != len(self.cards):
            return False
        
        for index, card_id in enumerate(valid_order):
            card_map[card_id].index = index
            card_map[card_id].updated_at = datetime.now().isoformat()
        
        self.sort_cards_by_index()
        self.updated_at = datetime.now().isoformat()
        return True

    def merge_cards(self, card_ids: List[str], new_text: str) -> Optional[StorylineCard]:
        if len(card_ids) < 2:
            return None
        
        card_map = {card.card_id: card for card in self.cards}
        cards_to_merge = [card_map.get(cid) for cid in card_ids if card_map.get(cid)]
        
        if len(cards_to_merge) < 2:
            return None
        
        cards_to_merge.sort(key=lambda c: c.index)
        min_index = cards_to_merge[0].index
        
        for card in cards_to_merge:
            self.cards.remove(card)
        
        merged_card = StorylineCard(
            card_id=f"card_{uuid.uuid4().hex[:8]}",
            text=new_text,
            index=min_index,
            tags=list(set(tag for card in cards_to_merge for tag in card.tags))
        )
        
        self.cards.append(merged_card)
        
        for i, card in enumerate(sorted(self.cards, key=lambda c: c.index)):
            card.index = i
        
        self.sort_cards_by_index()
        self.updated_at = datetime.now().isoformat()
        
        return merged_card

    def split_card(self, card_id: str, split_index: int, part1_text: str, part2_text: str) -> Optional[List[StorylineCard]]:
        card_map = {card.card_id: card for card in self.cards}
        original_card = card_map.get(card_id)
        
        if not original_card:
            return None
        
        self.cards.remove(original_card)
        
        card1 = StorylineCard(
            card_id=f"card_{uuid.uuid4().hex[:8]}",
            text=part1_text,
            index=original_card.index,
            tags=original_card.tags.copy()
        )
        
        card2 = StorylineCard(
            card_id=f"card_{uuid.uuid4().hex[:8]}",
            text=part2_text,
            index=original_card.index + 1,
            tags=original_card.tags.copy()
        )
        
        for card in self.cards:
            if card.index > original_card.index:
                card.index += 1
        
        self.cards.extend([card1, card2])
        self.sort_cards_by_index()
        self.updated_at = datetime.now().isoformat()
        
        return [card1, card2]

    def add_tags_to_card(self, card_id: str, tags: List[str]) -> bool:
        card_map = {card.card_id: card for card in self.cards}
        card = card_map.get(card_id)
        
        if not card:
            return False
        
        for tag in tags:
            if tag not in card.tags:
                card.tags.append(tag)
        
        card.updated_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        return True

    def remove_tags_from_card(self, card_id: str, tags: List[str]) -> bool:
        card_map = {card.card_id: card for card in self.cards}
        card = card_map.get(card_id)
        
        if not card:
            return False
        
        for tag in tags:
            if tag in card.tags:
                card.tags.remove(tag)
        
        card.updated_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        return True

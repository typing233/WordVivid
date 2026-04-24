import json
import uuid
import random
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

from config import get_settings
from models.card import MemoryCard
from services.volcengine_service import VolcEngineService


class GameType(str, Enum):
    IMAGE_TO_TEXT = "image_to_text"
    AUDIO_TO_TEXT = "audio_to_text"
    MIXED = "mixed"


class GameStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class GameCard:
    card_id: str
    text: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    similarity: Optional[float] = None
    answered_at: Optional[str] = None


@dataclass
class GameSession:
    game_id: str
    user_id: str
    game_type: str
    cards: List[GameCard] = field(default_factory=list)
    current_index: int = 0
    status: str = GameStatus.CREATED.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    total_correct: int = 0
    total_answered: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSession":
        cards_data = data.get("cards", [])
        cards = [GameCard(**card) for card in cards_data]
        return cls(
            game_id=data["game_id"],
            user_id=data["user_id"],
            game_type=data["game_type"],
            cards=cards,
            current_index=data.get("current_index", 0),
            status=data.get("status", GameStatus.CREATED.value),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            total_correct=data.get("total_correct", 0),
            total_answered=data.get("total_answered", 0)
        )


class GameService:
    def __init__(self, volcengine_service: Optional[VolcEngineService] = None):
        self.settings = get_settings()
        self.volcengine = volcengine_service or VolcEngineService()
        self._games: Dict[str, GameSession] = {}

    def _generate_game_id(self) -> str:
        return f"game_{uuid.uuid4().hex[:12]}"

    def _get_user_cards(self, user_id: str, card_ids: Optional[List[str]] = None) -> List[MemoryCard]:
        user_path = self.settings.CARDS_DIR / user_id
        
        if not user_path.exists():
            return []

        cards = []
        
        if card_ids:
            for card_id in card_ids:
                card_path = user_path / f"{card_id}.json"
                if card_path.exists():
                    try:
                        data = json.loads(card_path.read_text())
                        cards.append(MemoryCard.from_dict(data))
                    except Exception:
                        continue
        else:
            for card_file in user_path.glob("card_*.json"):
                try:
                    data = json.loads(card_file.read_text())
                    card = MemoryCard.from_dict(data)
                    if card.status == "completed" and (card.image or card.audio):
                        cards.append(card)
                except Exception:
                    continue

        return cards

    def start_game(
        self,
        user_id: str,
        game_type: str = GameType.IMAGE_TO_TEXT.value,
        card_ids: Optional[List[str]] = None,
        card_count: int = 10,
        shuffle: bool = True
    ) -> Dict[str, Any]:
        cards = self._get_user_cards(user_id, card_ids)
        
        if not cards:
            return {
                "success": False,
                "error": "没有可用的卡片，请先生成记忆卡片"
            }

        if shuffle:
            random.shuffle(cards)
        
        selected_cards = cards[:card_count]

        game_cards = []
        for card in selected_cards:
            game_card = GameCard(
                card_id=card.card_id,
                text=card.text,
                image_url=card.image.url if card.image else None,
                audio_url=card.audio.url if card.audio else None
            )
            game_cards.append(game_card)

        game_id = self._generate_game_id()
        session = GameSession(
            game_id=game_id,
            user_id=user_id,
            game_type=game_type,
            cards=game_cards,
            status=GameStatus.IN_PROGRESS.value
        )

        self._games[game_id] = session

        return {
            "success": True,
            "data": {
                "game_id": game_id,
                "total_cards": len(session.cards),
                "current_index": 0,
                "current_card": self._get_current_card_info(session),
                "game_type": game_type
            }
        }

    def _get_current_card_info(self, session: GameSession) -> Optional[Dict[str, Any]]:
        if session.current_index >= len(session.cards):
            return None

        card = session.cards[session.current_index]
        
        info = {
            "card_id": card.card_id,
            "index": session.current_index
        }

        if session.game_type == GameType.IMAGE_TO_TEXT.value:
            info["image_url"] = card.image_url
        elif session.game_type == GameType.AUDIO_TO_TEXT.value:
            info["audio_url"] = card.audio_url
        else:
            info["image_url"] = card.image_url
            info["audio_url"] = card.audio_url

        return info

    def get_current_card(self, game_id: str) -> Dict[str, Any]:
        session = self._games.get(game_id)
        
        if not session:
            return {
                "success": False,
                "error": "游戏会话不存在"
            }

        if session.status == GameStatus.COMPLETED.value:
            return {
                "success": True,
                "data": {
                    "game_id": game_id,
                    "status": session.status,
                    "total_cards": len(session.cards),
                    "total_answered": session.total_answered,
                    "total_correct": session.total_correct,
                    "correct_rate": round(session.total_correct / max(session.total_answered, 1), 2)
                }
            }

        return {
            "success": True,
            "data": {
                "game_id": game_id,
                "status": session.status,
                "total_cards": len(session.cards),
                "current_index": session.current_index,
                "current_card": self._get_current_card_info(session),
                "game_type": session.game_type,
                "total_answered": session.total_answered,
                "total_correct": session.total_correct
            }
        }

    def submit_answer(
        self,
        game_id: str,
        card_id: str,
        user_answer: str,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        session = self._games.get(game_id)
        
        if not session:
            return {
                "success": False,
                "error": "游戏会话不存在"
            }

        if session.status == GameStatus.COMPLETED.value:
            return {
                "success": False,
                "error": "游戏已结束"
            }

        if session.current_index >= len(session.cards):
            return {
                "success": False,
                "error": "没有更多卡片了"
            }

        current_card = session.cards[session.current_index]
        
        if current_card.card_id != card_id:
            return {
                "success": False,
                "error": f"卡片ID不匹配，当前应该回答的是卡片: {current_card.card_id}"
            }

        similarity = self.volcengine.calculate_similarity(
            user_answer,
            current_card.text
        )

        is_correct = similarity >= similarity_threshold

        current_card.user_answer = user_answer
        current_card.is_correct = is_correct
        current_card.similarity = similarity
        current_card.answered_at = datetime.now().isoformat()

        session.total_answered += 1
        if is_correct:
            session.total_correct += 1

        session.current_index += 1

        if session.current_index >= len(session.cards):
            session.status = GameStatus.COMPLETED.value
            session.completed_at = datetime.now().isoformat()

        next_card = None
        if session.current_index < len(session.cards):
            next_card = self._get_current_card_info(session)

        return {
            "success": True,
            "data": {
                "is_correct": is_correct,
                "correct_answer": current_card.text,
                "user_answer": user_answer,
                "similarity": round(similarity, 2),
                "next_card": next_card,
                "is_game_complete": session.status == GameStatus.COMPLETED.value,
                "current_stats": {
                    "total_answered": session.total_answered,
                    "total_correct": session.total_correct,
                    "correct_rate": round(session.total_correct / max(session.total_answered, 1), 2)
                }
            }
        }

    def get_game_results(self, game_id: str) -> Dict[str, Any]:
        session = self._games.get(game_id)
        
        if not session:
            return {
                "success": False,
                "error": "游戏会话不存在"
            }

        results = []
        for card in session.cards:
            results.append({
                "card_id": card.card_id,
                "text": card.text,
                "user_answer": card.user_answer,
                "is_correct": card.is_correct,
                "similarity": card.similarity,
                "answered_at": card.answered_at
            })

        correct_rate = 0.0
        if session.total_answered > 0:
            correct_rate = session.total_correct / session.total_answered

        return {
            "success": True,
            "data": {
                "game_id": game_id,
                "game_type": session.game_type,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at,
                "total_cards": len(session.cards),
                "total_answered": session.total_answered,
                "total_correct": session.total_correct,
                "correct_rate": round(correct_rate, 2),
                "results": results
            }
        }

    def list_user_games(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        user_games = [
            game for game in self._games.values()
            if game.user_id == user_id
        ]

        user_games.sort(key=lambda x: x.created_at, reverse=True)
        user_games = user_games[:limit]

        game_list = []
        for game in user_games:
            correct_rate = 0.0
            if game.total_answered > 0:
                correct_rate = game.total_correct / game.total_answered
            
            game_list.append({
                "game_id": game.game_id,
                "game_type": game.game_type,
                "status": game.status,
                "created_at": game.created_at,
                "total_cards": len(game.cards),
                "total_correct": game.total_correct,
                "correct_rate": round(correct_rate, 2)
            })

        return {
            "success": True,
            "data": {
                "games": game_list
            }
        }

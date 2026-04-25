import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


class WriterType(str, Enum):
    USER = "user"
    AI = "ai"


class BranchStatus(str, Enum):
    DRAFT = "draft"
    SELECTED = "selected"
    REJECTED = "rejected"


@dataclass
class WritingSegment:
    segment_id: str
    content: str
    writer: str
    writer_type: str
    order: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WritingSegment":
        return cls(
            segment_id=data["segment_id"],
            content=data["content"],
            writer=data["writer"],
            writer_type=data["writer_type"],
            order=data["order"],
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


@dataclass
class WritingBranch:
    branch_id: str
    parent_segment_id: str
    content: str
    description: Optional[str] = None
    status: str = BranchStatus.DRAFT.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WritingBranch":
        return cls(
            branch_id=data["branch_id"],
            parent_segment_id=data["parent_segment_id"],
            content=data["content"],
            description=data.get("description"),
            status=data.get("status", BranchStatus.DRAFT.value),
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


@dataclass
class Character:
    character_id: str
    name: str
    description: str
    personality: Optional[str] = None
    background: Optional[str] = None
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        return cls(
            character_id=data["character_id"],
            name=data["name"],
            description=data["description"],
            personality=data.get("personality"),
            background=data.get("background"),
            relationships=data.get("relationships", []),
            traits=data.get("traits", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class WorldSetting:
    setting_id: str
    name: str
    description: str
    genre: Optional[str] = None
    era: Optional[str] = None
    rules: List[str] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    lore: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldSetting":
        return cls(
            setting_id=data["setting_id"],
            name=data["name"],
            description=data["description"],
            genre=data.get("genre"),
            era=data.get("era"),
            rules=data.get("rules", []),
            locations=data.get("locations", []),
            lore=data.get("lore"),
            metadata=data.get("metadata", {})
        )


@dataclass
class WritingStyle:
    style_id: str
    name: str
    type: str
    description: str
    prompt_template: str
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WritingStyle":
        return cls(
            style_id=data["style_id"],
            name=data["name"],
            type=data["type"],
            description=data["description"],
            prompt_template=data["prompt_template"],
            examples=data.get("examples", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class CollabWritingSession:
    session_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    segments: List[WritingSegment] = field(default_factory=list)
    branches: List[WritingBranch] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    world_settings: List[WorldSetting] = field(default_factory=list)
    selected_style: Optional[WritingStyle] = None
    last_writer: str = WriterType.USER.value
    turn_count: int = 0
    is_alternating: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["segments"] = [s.to_dict() for s in self.segments]
        data["branches"] = [b.to_dict() for b in self.branches]
        data["characters"] = [c.to_dict() for c in self.characters]
        data["world_settings"] = [w.to_dict() for w in self.world_settings]
        if self.selected_style:
            data["selected_style"] = self.selected_style.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollabWritingSession":
        segments_data = data.get("segments", [])
        branches_data = data.get("branches", [])
        characters_data = data.get("characters", [])
        world_settings_data = data.get("world_settings", [])
        style_data = data.get("selected_style")

        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            title=data["title"],
            description=data.get("description"),
            segments=[WritingSegment.from_dict(s) for s in segments_data],
            branches=[WritingBranch.from_dict(b) for b in branches_data],
            characters=[Character.from_dict(c) for c in characters_data],
            world_settings=[WorldSetting.from_dict(w) for w in world_settings_data],
            selected_style=WritingStyle.from_dict(style_data) if style_data else None,
            last_writer=data.get("last_writer", WriterType.USER.value),
            turn_count=data.get("turn_count", 0),
            is_alternating=data.get("is_alternating", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )

    def add_segment(self, content: str, writer: str, writer_type: str) -> WritingSegment:
        segment = WritingSegment(
            segment_id=f"seg_{uuid.uuid4().hex[:8]}",
            content=content,
            writer=writer,
            writer_type=writer_type,
            order=len(self.segments)
        )
        self.segments.append(segment)
        self.last_writer = writer_type
        self.turn_count += 1
        self.updated_at = datetime.now().isoformat()
        return segment

    def add_branch(self, parent_segment_id: str, content: str, description: Optional[str] = None) -> WritingBranch:
        branch = WritingBranch(
            branch_id=f"br_{uuid.uuid4().hex[:8]}",
            parent_segment_id=parent_segment_id,
            content=content,
            description=description
        )
        self.branches.append(branch)
        self.updated_at = datetime.now().isoformat()
        return branch

    def select_branch(self, branch_id: str) -> Optional[WritingSegment]:
        branch_map = {b.branch_id: b for b in self.branches}
        branch = branch_map.get(branch_id)
        
        if not branch:
            return None

        for b in self.branches:
            if b.branch_id == branch_id:
                b.status = BranchStatus.SELECTED.value
            elif b.parent_segment_id == branch.parent_segment_id:
                b.status = BranchStatus.REJECTED.value

        segment = self.add_segment(
            content=branch.content,
            writer="AI",
            writer_type=WriterType.AI.value
        )
        segment.metadata["from_branch"] = branch_id
        
        return segment

    def add_character(self, name: str, description: str, personality: Optional[str] = None, 
                      background: Optional[str] = None, traits: Optional[List[str]] = None) -> Character:
        character = Character(
            character_id=f"char_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            personality=personality,
            background=background,
            traits=traits or []
        )
        self.characters.append(character)
        self.updated_at = datetime.now().isoformat()
        return character

    def add_world_setting(self, name: str, description: str, genre: Optional[str] = None,
                          era: Optional[str] = None, rules: Optional[List[str]] = None) -> WorldSetting:
        setting = WorldSetting(
            setting_id=f"set_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            genre=genre,
            era=era,
            rules=rules or []
        )
        self.world_settings.append(setting)
        self.updated_at = datetime.now().isoformat()
        return setting

    def get_context_for_ai(self) -> str:
        context_parts = []
        
        if self.title:
            context_parts.append(f"故事标题: {self.title}")
        
        if self.description:
            context_parts.append(f"故事描述: {self.description}")
        
        if self.world_settings:
            context_parts.append("\n世界观设定:")
            for setting in self.world_settings:
                context_parts.append(f"- {setting.name}: {setting.description}")
                if setting.genre:
                    context_parts.append(f"  类型: {setting.genre}")
                if setting.era:
                    context_parts.append(f"  时代: {setting.era}")
                if setting.rules:
                    context_parts.append(f"  规则: {', '.join(setting.rules)}")
        
        if self.characters:
            context_parts.append("\n角色设定:")
            for char in self.characters:
                context_parts.append(f"- {char.name}: {char.description}")
                if char.personality:
                    context_parts.append(f"  性格: {char.personality}")
                if char.background:
                    context_parts.append(f"  背景: {char.background}")
                if char.traits:
                    context_parts.append(f"  特点: {', '.join(char.traits)}")
        
        if self.segments:
            context_parts.append("\n已写内容:")
            for seg in self.segments:
                writer_label = "用户" if seg.writer_type == WriterType.USER.value else "AI"
                context_parts.append(f"[{writer_label}]: {seg.content}")
        
        return "\n".join(context_parts)

    def sort_segments(self):
        self.segments.sort(key=lambda s: s.order)

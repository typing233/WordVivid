import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


class EmotionType(str, Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    ANTICIPATION = "anticipation"
    TRUST = "trust"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


class PlotElementType(str, Enum):
    EXPOSITION = "exposition"
    RISING_ACTION = "rising_action"
    CLIMAX = "climax"
    FALLING_ACTION = "falling_action"
    RESOLUTION = "resolution"
    TURNING_POINT = "turning_point"


@dataclass
class EmotionPoint:
    segment_id: str
    position: float
    emotion_type: str
    intensity: float
    secondary_emotions: List[Dict[str, float]] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionPoint":
        return cls(
            segment_id=data["segment_id"],
            position=data["position"],
            emotion_type=data["emotion_type"],
            intensity=data["intensity"],
            secondary_emotions=data.get("secondary_emotions", []),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class PlotPoint:
    segment_id: str
    position: float
    plot_type: str
    tension_level: float
    description: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlotPoint":
        return cls(
            segment_id=data["segment_id"],
            position=data["position"],
            plot_type=data["plot_type"],
            tension_level=data["tension_level"],
            description=data.get("description"),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class CharacterNode:
    character_id: str
    name: str
    segment_ids: List[str] = field(default_factory=list)
    mentions: int = 0
    sentiment: float = 0.0
    importance: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0
    color: str = "#6366f1"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterNode":
        return cls(
            character_id=data["character_id"],
            name=data["name"],
            segment_ids=data.get("segment_ids", []),
            mentions=data.get("mentions", 0),
            sentiment=data.get("sentiment", 0.0),
            importance=data.get("importance", 0.0),
            attributes=data.get("attributes", {}),
            position_x=data.get("position_x", 0.0),
            position_y=data.get("position_y", 0.0),
            color=data.get("color", "#6366f1")
        )


@dataclass
class RelationshipEdge:
    edge_id: str
    from_character_id: str
    to_character_id: str
    relationship_type: str
    strength: float
    sentiment: float
    segment_ids: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipEdge":
        return cls(
            edge_id=data["edge_id"],
            from_character_id=data["from_character_id"],
            to_character_id=data["to_character_id"],
            relationship_type=data["relationship_type"],
            strength=data["strength"],
            sentiment=data["sentiment"],
            segment_ids=data.get("segment_ids", []),
            description=data.get("description")
        )


@dataclass
class ArgumentNode:
    argument_id: str
    content: str
    segment_id: str
    position: float
    argument_type: str
    supporting_points: List[str] = field(default_factory=list)
    counter_points: List[str] = field(default_factory=list)
    weight: float = 0.5
    position_x: float = 0.0
    position_y: float = 0.0
    color: str = "#10b981"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArgumentNode":
        return cls(
            argument_id=data["argument_id"],
            content=data["content"],
            segment_id=data["segment_id"],
            position=data["position"],
            argument_type=data["argument_type"],
            supporting_points=data.get("supporting_points", []),
            counter_points=data.get("counter_points", []),
            weight=data.get("weight", 0.5),
            position_x=data.get("position_x", 0.0),
            position_y=data.get("position_y", 0.0),
            color=data.get("color", "#10b981")
        )


@dataclass
class ArgumentEdge:
    edge_id: str
    from_argument_id: str
    to_argument_id: str
    relation_type: str
    strength: float
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArgumentEdge":
        return cls(
            edge_id=data["edge_id"],
            from_argument_id=data["from_argument_id"],
            to_argument_id=data["to_argument_id"],
            relation_type=data["relation_type"],
            strength=data["strength"],
            description=data.get("description")
        )


@dataclass
class VividMirrorAnalysis:
    analysis_id: str
    user_id: str
    source_type: str
    source_id: str
    title: str
    
    emotion_points: List[EmotionPoint] = field(default_factory=list)
    plot_points: List[PlotPoint] = field(default_factory=list)
    character_nodes: List[CharacterNode] = field(default_factory=list)
    character_edges: List[RelationshipEdge] = field(default_factory=list)
    argument_nodes: List[ArgumentNode] = field(default_factory=list)
    argument_edges: List[ArgumentEdge] = field(default_factory=list)
    
    summary: Optional[str] = None
    themes: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["emotion_points"] = [ep.to_dict() for ep in self.emotion_points]
        data["plot_points"] = [pp.to_dict() for pp in self.plot_points]
        data["character_nodes"] = [cn.to_dict() for cn in self.character_nodes]
        data["character_edges"] = [ce.to_dict() for ce in self.character_edges]
        data["argument_nodes"] = [an.to_dict() for an in self.argument_nodes]
        data["argument_edges"] = [ae.to_dict() for ae in self.argument_edges]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VividMirrorAnalysis":
        ep_data = data.get("emotion_points", [])
        pp_data = data.get("plot_points", [])
        cn_data = data.get("character_nodes", [])
        ce_data = data.get("character_edges", [])
        an_data = data.get("argument_nodes", [])
        ae_data = data.get("argument_edges", [])

        return cls(
            analysis_id=data["analysis_id"],
            user_id=data["user_id"],
            source_type=data["source_type"],
            source_id=data["source_id"],
            title=data["title"],
            emotion_points=[EmotionPoint.from_dict(ep) for ep in ep_data],
            plot_points=[PlotPoint.from_dict(pp) for pp in pp_data],
            character_nodes=[CharacterNode.from_dict(cn) for cn in cn_data],
            character_edges=[RelationshipEdge.from_dict(ce) for ce in ce_data],
            argument_nodes=[ArgumentNode.from_dict(an) for an in an_data],
            argument_edges=[ArgumentEdge.from_dict(ae) for ae in ae_data],
            summary=data.get("summary"),
            themes=data.get("themes", []),
            keywords=data.get("keywords", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )

    def get_emotion_heatmap_data(self) -> Dict[str, Any]:
        positions = []
        intensities = []
        emotions = []
        
        for ep in sorted(self.emotion_points, key=lambda x: x.position):
            positions.append(ep.position)
            intensities.append(ep.intensity)
            emotions.append(ep.emotion_type)
        
        return {
            "positions": positions,
            "intensities": intensities,
            "emotions": emotions,
            "color_map": {
                "joy": "#fbbf24",
                "sadness": "#3b82f6",
                "anger": "#ef4444",
                "fear": "#8b5cf6",
                "surprise": "#06b6d4",
                "anticipation": "#f97316",
                "trust": "#10b981",
                "disgust": "#84cc16",
                "neutral": "#9ca3af"
            }
        }

    def get_plot_heatmap_data(self) -> Dict[str, Any]:
        positions = []
        tensions = []
        plot_types = []
        
        for pp in sorted(self.plot_points, key=lambda x: x.position):
            positions.append(pp.position)
            tensions.append(pp.tension_level)
            plot_types.append(pp.plot_type)
        
        return {
            "positions": positions,
            "tensions": tensions,
            "plot_types": plot_types,
            "type_labels": {
                "exposition": "序幕",
                "rising_action": "上升",
                "climax": "高潮",
                "falling_action": "下降",
                "resolution": "结局",
                "turning_point": "转折"
            }
        }

    def get_character_graph_data(self) -> Dict[str, Any]:
        nodes = []
        for node in self.character_nodes:
            nodes.append({
                "id": node.character_id,
                "label": node.name,
                "mentions": node.mentions,
                "importance": node.importance,
                "sentiment": node.sentiment,
                "x": node.position_x,
                "y": node.position_y,
                "color": node.color,
                "size": max(20, min(60, 20 + node.importance * 40))
            })
        
        edges = []
        for edge in self.character_edges:
            edges.append({
                "id": edge.edge_id,
                "from": edge.from_character_id,
                "to": edge.to_character_id,
                "type": edge.relationship_type,
                "strength": edge.strength,
                "sentiment": edge.sentiment,
                "width": max(1, min(5, 1 + edge.strength * 4))
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }

    def get_argument_graph_data(self) -> Dict[str, Any]:
        nodes = []
        for node in self.argument_nodes:
            nodes.append({
                "id": node.argument_id,
                "label": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                "content": node.content,
                "type": node.argument_type,
                "weight": node.weight,
                "x": node.position_x,
                "y": node.position_y,
                "color": node.color,
                "size": max(20, min(50, 20 + node.weight * 30))
            })
        
        edges = []
        for edge in self.argument_edges:
            edges.append({
                "id": edge.edge_id,
                "from": edge.from_argument_id,
                "to": edge.to_argument_id,
                "type": edge.relation_type,
                "strength": edge.strength,
                "arrow": True
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }

    def calculate_node_positions(self):
        import math
        
        char_count = len(self.character_nodes)
        for i, node in enumerate(self.character_nodes):
            angle = 2 * math.pi * i / char_count
            radius = 150 + (node.importance * 50)
            node.position_x = 250 + radius * math.cos(angle)
            node.position_y = 250 + radius * math.sin(angle)
        
        colors = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#06b6d4", "#8b5cf6", "#ef4444", "#84cc16"]
        for i, node in enumerate(self.character_nodes):
            node.color = colors[i % len(colors)]

        arg_count = len(self.argument_nodes)
        for i, node in enumerate(self.argument_nodes):
            angle = 2 * math.pi * i / arg_count if arg_count > 0 else 0
            radius = 120
            node.position_x = 250 + radius * math.cos(angle)
            node.position_y = 250 + radius * math.sin(angle)

        arg_colors = ["#10b981", "#6366f1", "#f59e0b", "#06b6d4", "#8b5cf6"]
        for i, node in enumerate(self.argument_nodes):
            node.color = arg_colors[i % len(arg_colors)]

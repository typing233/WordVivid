import json
import uuid
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime

from config import get_settings
from models.vivid_mirror import (
    VividMirrorAnalysis, EmotionPoint, PlotPoint, CharacterNode,
    RelationshipEdge, ArgumentNode, ArgumentEdge, EmotionType, PlotElementType
)
from services.volcengine_service import VolcEngineService, ChatMessage


class VividMirrorService:
    def __init__(self):
        self.settings = get_settings()
        self.analyses_dir = self.settings.DATA_DIR / "vivid_analyses"
        self.analyses_dir.mkdir(parents=True, exist_ok=True)
        
        self.emotion_keywords = {
            "joy": ["快乐", "高兴", "开心", "幸福", "喜悦", "欢笑", "笑容", "愉快", "欢乐", "兴高采烈", "喜气洋洋"],
            "sadness": ["悲伤", "难过", "伤心", "痛苦", "哭泣", "泪水", "忧愁", "哀伤", "悲痛", "心如刀割", "泪如雨下"],
            "anger": ["愤怒", "生气", "恼火", "气愤", "怒吼", "咆哮", "怒火", "愤怒", "勃然大怒", "火冒三丈"],
            "fear": ["恐惧", "害怕", "惊恐", "畏惧", "颤抖", "惊慌", "恐惧", "心惊胆战", "毛骨悚然", "不寒而栗"],
            "surprise": ["惊讶", "惊奇", "震惊", "意外", "突然", "诧异", "目瞪口呆", "大吃一惊", "出乎意料"],
            "anticipation": ["期待", "盼望", "等待", "渴望", "向往", "憧憬", "迫不及待", "望眼欲穿"],
            "trust": ["信任", "相信", "信赖", "忠诚", "诚实", "可靠", "真心实意", "肝胆相照"],
            "disgust": ["厌恶", "反感", "恶心", "讨厌", "嫌弃", "憎恶", "令人作呕", "嗤之以鼻"]
        }

    def create_analysis(
        self,
        user_id: str,
        source_type: str,
        source_id: str,
        title: str,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        analysis_id = f"vm_{uuid.uuid4().hex[:8]}"
        
        analysis = VividMirrorAnalysis(
            analysis_id=analysis_id,
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            title=title
        )

        total_segments = len(segments)
        if total_segments > 0:
            for i, segment in enumerate(segments):
                segment_id = segment.get("segment_id", f"seg_{i}")
                text = segment.get("text", "")
                position = (i + 0.5) / total_segments

                emotion_point = self._analyze_emotion(segment_id, position, text)
                analysis.emotion_points.append(emotion_point)

                plot_point = self._analyze_plot(segment_id, position, text, i, total_segments)
                analysis.plot_points.append(plot_point)

                self._extract_characters(analysis, segment_id, text, position)
                self._extract_arguments(analysis, segment_id, text, position)

        analysis.calculate_node_positions()
        analysis.updated_at = datetime.now().isoformat()

        self._save_analysis(analysis)

        return {
            "success": True,
            "data": self._analysis_to_response(analysis)
        }

    def _analyze_emotion(self, segment_id: str, position: float, text: str) -> EmotionPoint:
        emotion_counts = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            count = 0
            for keyword in keywords:
                count += text.count(keyword)
            if count > 0:
                emotion_counts[emotion] = count

        if emotion_counts:
            primary_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            total_count = sum(emotion_counts.values())
            intensity = min(1.0, total_count / 5)
            
            secondary_emotions = [
                {"emotion": e, "intensity": c / total_count if total_count > 0 else 0}
                for e, c in emotion_counts.items() if e != primary_emotion
            ]
            
            return EmotionPoint(
                segment_id=segment_id,
                position=position,
                emotion_type=primary_emotion,
                intensity=intensity,
                secondary_emotions=secondary_emotions
            )
        else:
            return EmotionPoint(
                segment_id=segment_id,
                position=position,
                emotion_type=EmotionType.NEUTRAL.value,
                intensity=0.3
            )

    def _analyze_plot(
        self,
        segment_id: str,
        position: float,
        text: str,
        index: int,
        total: int
    ) -> PlotPoint:
        tension_keywords = ["突然", "忽然", "就在这时", "然而", "但是", "不料", "没想到", "危机", "危险", "紧急"]
        climax_keywords = ["终于", "最后", "高潮", "决战", "真相大白", "原来如此", "关键时刻"]
        resolution_keywords = ["从此", "于是", "最后", "结局", "圆满", "结束", "落幕"]
        
        tension_count = sum(1 for kw in tension_keywords if kw in text)
        
        plot_type = PlotElementType.RISING_ACTION.value
        
        if position < 0.15:
            plot_type = PlotElementType.EXPOSITION.value
            tension_level = 0.2
        elif position > 0.85:
            plot_type = PlotElementType.RESOLUTION.value
            tension_level = 0.3
        elif 0.4 < position < 0.6:
            if any(kw in text for kw in climax_keywords):
                plot_type = PlotElementType.CLIMAX.value
                tension_level = 0.9
            else:
                plot_type = PlotElementType.RISING_ACTION.value
                tension_level = 0.5 + min(0.3, tension_count * 0.1)
        else:
            if any(kw in text for kw in ["突然", "忽然", "然而", "但是", "不料"]):
                plot_type = PlotElementType.TURNING_POINT.value
                tension_level = 0.7
            else:
                plot_type = PlotElementType.RISING_ACTION.value
                tension_level = 0.4 + min(0.3, tension_count * 0.1)

        return PlotPoint(
            segment_id=segment_id,
            position=position,
            plot_type=plot_type,
            tension_level=tension_level,
            description=f"第 {index + 1} 段"
        )

    def _extract_characters(
        self,
        analysis: VividMirrorAnalysis,
        segment_id: str,
        text: str,
        position: float
    ):
        existing_chars = {node.name: node for node in analysis.character_nodes}
        
        name_patterns = [
            r'([\u4e00-\u9fa5]{2,4})(说|道|问|答|想|看|听)',
            r'([\u4e00-\u9fa5]{2,4})先生',
            r'([\u4e00-\u9fa5]{2,4})小姐',
            r'([\u4e00-\u9fa5]{2,4})夫人',
        ]
        
        found_names = set()
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match[0] if isinstance(match, tuple) else match
                if len(name) >= 2 and len(name) <= 4:
                    found_names.add(name)
        
        for name in found_names:
            if name in existing_chars:
                node = existing_chars[name]
                node.mentions += 1
                if segment_id not in node.segment_ids:
                    node.segment_ids.append(segment_id)
            else:
                new_node = CharacterNode(
                    character_id=f"char_{uuid.uuid4().hex[:6]}",
                    name=name,
                    mentions=1,
                    importance=0.5,
                    sentiment=0.0,
                    segment_ids=[segment_id]
                )
                analysis.character_nodes.append(new_node)

    def _extract_arguments(
        self,
        analysis: VividMirrorAnalysis,
        segment_id: str,
        text: str,
        position: float
    ):
        argument_indicators = [
            "因为", "所以", "因此", "由此可见", "综上所述",
            "我认为", "应该", "必须", "需要", "重要的是",
            "首先", "其次", "最后", "第一", "第二", "第三"
        ]
        
        has_argument = any(ind in text for ind in argument_indicators)
        
        if has_argument or len(text) > 100:
            sentences = re.split(r'[。！？.!?]+', text)
            for sent in sentences:
                if len(sent.strip()) > 20:
                    arg_type = "claim" if any(ind in sent for ind in ["我认为", "应该", "必须", "需要"]) else "evidence"
                    
                    node = ArgumentNode(
                        argument_id=f"arg_{uuid.uuid4().hex[:6]}",
                        content=sent.strip(),
                        segment_id=segment_id,
                        position=position,
                        argument_type=arg_type,
                        weight=0.5
                    )
                    analysis.argument_nodes.append(node)

    async def analyze_with_ai(
        self,
        user_id: str,
        source_type: str,
        source_id: str,
        title: str,
        segments: List[Dict[str, Any]],
        volcengine_service: VolcEngineService
    ) -> Dict[str, Any]:
        basic_result = self.create_analysis(user_id, source_type, source_id, title, segments)
        
        if not basic_result["success"]:
            return basic_result
        
        analysis_id = basic_result["data"]["analysis_id"]
        analysis = self._load_analysis(user_id, analysis_id)
        
        if not analysis:
            return basic_result

        try:
            context = "\n".join([
                f"第{i+1}段: {seg.get('text', '')[:200]}"
                for i, seg in enumerate(segments)
            ])

            system_prompt = """你是一个文本分析专家。请分析以下文本内容，提取：
1. 主要人物及其关系
2. 核心论点及其逻辑关系
3. 情感变化趋势
4. 情节结构特点

请以JSON格式返回分析结果，包含以下字段：
- characters: 人物列表，每个包含name, description, importance(0-1)
- relationships: 关系列表，每个包含from, to, type, strength(0-1)
- arguments: 论点列表，每个包含content, type(claim/evidence), weight(0-1)
- themes: 主题列表
- summary: 简要总结

只返回JSON，不要其他内容。"""

            user_prompt = f"请分析以下文本：\n\n{context}"

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]

            result = volcengine_service.chat_completion(
                messages,
                temperature=0.3,
                max_tokens=2000
            )

            if result.success and result.content:
                try:
                    ai_analysis = json.loads(result.content)
                    
                    existing_chars = {node.name: node for node in analysis.character_nodes}
                    for char_data in ai_analysis.get("characters", []):
                        name = char_data.get("name", "")
                        if name in existing_chars:
                            existing_chars[name].importance = char_data.get("importance", 0.5)
                            existing_chars[name].attributes["ai_description"] = char_data.get("description", "")
                        else:
                            new_node = CharacterNode(
                                character_id=f"char_{uuid.uuid4().hex[:6]}",
                                name=name,
                                importance=char_data.get("importance", 0.5),
                                attributes={"ai_description": char_data.get("description", "")}
                            )
                            analysis.character_nodes.append(new_node)

                    for rel_data in ai_analysis.get("relationships", []):
                        from_name = rel_data.get("from", "")
                        to_name = rel_data.get("to", "")
                        
                        from_char = next((c for c in analysis.character_nodes if c.name == from_name), None)
                        to_char = next((c for c in analysis.character_nodes if c.name == to_name), None)
                        
                        if from_char and to_char:
                            edge = RelationshipEdge(
                                edge_id=f"edge_{uuid.uuid4().hex[:6]}",
                                from_character_id=from_char.character_id,
                                to_character_id=to_char.character_id,
                                relationship_type=rel_data.get("type", "unknown"),
                                strength=rel_data.get("strength", 0.5),
                                sentiment=0.0
                            )
                            analysis.character_edges.append(edge)

                    analysis.themes = ai_analysis.get("themes", [])
                    analysis.summary = ai_analysis.get("summary", "")

                    analysis.calculate_node_positions()
                    analysis.updated_at = datetime.now().isoformat()
                    self._save_analysis(analysis)

                except json.JSONDecodeError:
                    pass

        except Exception:
            pass

        return {
            "success": True,
            "data": self._analysis_to_response(analysis)
        }

    def get_analysis(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None
        return {
            "success": True,
            "data": self._analysis_to_response(analysis)
        }

    def list_analyses(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        user_path = self._get_user_analyses_path(user_id)
        
        analyses = []
        for an_file in user_path.glob("vm_*.json"):
            try:
                data = json.loads(an_file.read_text())
                analysis = VividMirrorAnalysis.from_dict(data)
                analyses.append(analysis)
            except Exception:
                continue

        analyses.sort(key=lambda a: a.updated_at, reverse=True)

        total = len(analyses)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated = analyses[start:end]

        return {
            "success": True,
            "data": {
                "analyses": [self._analysis_to_response(a, include_details=False) for a in paginated],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }

    def get_emotion_heatmap(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None
        return {
            "success": True,
            "data": analysis.get_emotion_heatmap_data()
        }

    def get_plot_heatmap(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None
        return {
            "success": True,
            "data": analysis.get_plot_heatmap_data()
        }

    def get_character_graph(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None
        return {
            "success": True,
            "data": analysis.get_character_graph_data()
        }

    def get_argument_graph(self, user_id: str, analysis_id: str) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None
        return {
            "success": True,
            "data": analysis.get_argument_graph_data()
        }

    def find_segment_by_node(
        self,
        user_id: str,
        analysis_id: str,
        node_type: str,
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        analysis = self._load_analysis(user_id, analysis_id)
        if not analysis:
            return None

        segment_id = None
        
        if node_type == "character":
            for node in analysis.character_nodes:
                if node.character_id == node_id:
                    if node.segment_ids:
                        segment_id = node.segment_ids[0]
                    break
        elif node_type == "argument":
            for node in analysis.argument_nodes:
                if node.argument_id == node_id:
                    segment_id = node.segment_id
                    break
        elif node_type == "emotion":
            for point in analysis.emotion_points:
                if point.segment_id == node_id:
                    segment_id = node_id
                    break
        elif node_type == "plot":
            for point in analysis.plot_points:
                if point.segment_id == node_id:
                    segment_id = node_id
                    break

        if segment_id:
            return {
                "success": True,
                "data": {
                    "segment_id": segment_id,
                    "node_type": node_type,
                    "node_id": node_id
                }
            }
        
        return None

    def delete_analysis(self, user_id: str, analysis_id: str) -> Dict[str, Any]:
        user_path = self._get_user_analyses_path(user_id)
        an_file = user_path / f"{analysis_id}.json"
        
        if not an_file.exists():
            return {
                "success": False,
                "error": "分析不存在"
            }

        try:
            an_file.unlink()
            return {
                "success": True,
                "message": "分析已删除"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除分析失败: {str(e)}"
            }

    def _get_user_analyses_path(self, user_id: str) -> Path:
        user_path = self.analyses_dir / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def _load_analysis(self, user_id: str, analysis_id: str) -> Optional[VividMirrorAnalysis]:
        user_path = self._get_user_analyses_path(user_id)
        an_file = user_path / f"{analysis_id}.json"
        
        if not an_file.exists():
            return None

        try:
            data = json.loads(an_file.read_text())
            return VividMirrorAnalysis.from_dict(data)
        except Exception:
            return None

    def _save_analysis(self, analysis: VividMirrorAnalysis):
        user_path = self._get_user_analyses_path(analysis.user_id)
        an_file = user_path / f"{analysis.analysis_id}.json"
        
        with open(an_file, 'w', encoding='utf-8') as f:
            json.dump(analysis.to_dict(), f, ensure_ascii=False, indent=2)

    def _analysis_to_response(self, analysis: VividMirrorAnalysis, include_details: bool = True) -> Dict[str, Any]:
        response = {
            "analysis_id": analysis.analysis_id,
            "source_type": analysis.source_type,
            "source_id": analysis.source_id,
            "title": analysis.title,
            "summary": analysis.summary,
            "themes": analysis.themes,
            "keywords": analysis.keywords,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at
        }

        if include_details:
            response.update({
                "emotion_heatmap": analysis.get_emotion_heatmap_data(),
                "plot_heatmap": analysis.get_plot_heatmap_data(),
                "character_graph": analysis.get_character_graph_data(),
                "argument_graph": analysis.get_argument_graph_data(),
                "emotion_points_count": len(analysis.emotion_points),
                "plot_points_count": len(analysis.plot_points),
                "character_count": len(analysis.character_nodes),
                "argument_count": len(analysis.argument_nodes)
            })

        return response

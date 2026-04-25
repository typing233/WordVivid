import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from config import get_settings
from models.collab_writing import (
    CollabWritingSession, WriterType, WritingStyle, Character, WorldSetting
)
from services.volcengine_service import VolcEngineService, ChatMessage


class CollabWritingService:
    def __init__(self):
        self.settings = get_settings()
        self.sessions_dir = self.settings.DATA_DIR / "collab_sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.preset_styles = self._load_preset_styles()
        self.preset_world_settings = self._load_preset_world_settings()

    def _load_preset_styles(self) -> Dict[str, WritingStyle]:
        styles = {
            "lock_user": WritingStyle(
                style_id="lock_user",
                name="锁定用户文风",
                type="custom",
                description="分析并模仿用户的写作风格，保持一致性",
                prompt_template="请分析以下用户写作风格并续写：\n{user_style_analysis}\n\n续写要求：保持与用户相同的用词习惯、句式结构和情感基调。",
                examples=[]
            ),
            "lu_xun": WritingStyle(
                style_id="lu_xun",
                name="鲁迅风格",
                type="author",
                description="模仿鲁迅的写作风格：犀利、讽刺、深刻的社会批判",
                prompt_template="请模仿鲁迅的写作风格续写。鲁迅风格特点：\n1. 语言犀利，带有讽刺意味\n2. 深刻的社会批判和人性洞察\n3. 常用比喻、象征手法\n4. 句式凝练，富有张力\n\n续写：",
                examples=[
                    "真的猛士，敢于直面惨淡的人生，敢于正视淋漓的鲜血。",
                    "世上本没有路，走的人多了，也便成了路。"
                ]
            ),
            "jin_yong": WritingStyle(
                style_id="jin_yong",
                name="金庸风格",
                type="author",
                description="模仿金庸的武侠小说风格：大气磅礴、诗意盎然",
                prompt_template="请模仿金庸的武侠写作风格续写。金庸风格特点：\n1. 大气磅礴的场景描写\n2. 诗意盎然的人物刻画\n3. 融合传统文化与武侠精神\n4. 情节跌宕起伏，扣人心弦\n\n续写：",
                examples=[
                    "侠之大者，为国为民。",
                    "他强由他强，清风拂山岗；他横由他横，明月照大江。"
                ]
            ),
            "zhang_ailing": WritingStyle(
                style_id="zhang_ailing",
                name="张爱玲风格",
                type="author",
                description="模仿张爱玲的写作风格：细腻、苍凉、都市风情",
                prompt_template="请模仿张爱玲的写作风格续写。张爱玲风格特点：\n1. 细腻入微的心理描写\n2. 苍凉悲剧的基调\n3. 都市男女的情感纠葛\n4. 精致的意象和比喻\n\n续写：",
                examples=[
                    "生命是一袭华美的袍，爬满了蚤子。",
                    "于千万人之中遇见你所要遇见的人，于千万年之中，时间的无涯的荒野里，没有早一步，也没有晚一步，刚巧赶上了。"
                ]
            ),
            "mo_yan": WritingStyle(
                style_id="mo_yan",
                name="莫言风格",
                type="author",
                description="模仿莫言的魔幻现实主义风格：狂野、魔幻、乡土",
                prompt_template="请模仿莫言的魔幻现实主义写作风格续写。莫言风格特点：\n1. 魔幻与现实的融合\n2. 狂野奔放的语言\n3. 乡土气息与民间传说\n4. 夸张变形的叙事手法\n\n续写：",
                examples=[
                    "当众人都哭时，应该允许有的人不哭。",
                    "所谓的爱情，不过是化学反应的副产品。"
                ]
            ),
            "poetic": WritingStyle(
                style_id="poetic",
                name="诗意风格",
                type="genre",
                description="富有诗意和韵律感的写作风格",
                prompt_template="请用诗意的风格续写。特点：\n1. 语言优美，富有韵律\n2. 意象丰富，意境深远\n3. 情感细腻，含蓄委婉\n4. 句式灵活，富有节奏感\n\n续写：",
                examples=[]
            ),
            "dramatic": WritingStyle(
                style_id="dramatic",
                name="戏剧风格",
                type="genre",
                description="富有戏剧性和张力的写作风格",
                prompt_template="请用戏剧化的风格续写。特点：\n1. 情节紧凑，冲突激烈\n2. 对话生动，性格鲜明\n3. 悬念迭起，扣人心弦\n4. 场景描写富有画面感\n\n续写：",
                examples=[]
            ),
            "philosophical": WritingStyle(
                style_id="philosophical",
                name="哲思风格",
                type="genre",
                description="富有哲理和思辨的写作风格",
                prompt_template="请用哲思的风格续写。特点：\n1. 深入思考，富有洞见\n2. 逻辑严密，论证清晰\n3. 探讨人生、存在等深层问题\n4. 语言简洁而富有深意\n\n续写：",
                examples=[]
            )
        }
        return styles

    def _load_preset_world_settings(self) -> Dict[str, Dict[str, Any]]:
        return {
            "xianxia": {
                "name": "仙侠世界",
                "description": "东方仙侠玄幻世界，有修仙、门派、法宝、天劫等设定",
                "genre": "仙侠玄幻",
                "rules": [
                    "存在修仙境界划分（如：炼气、筑基、金丹、元婴等）",
                    "有门派势力和江湖恩怨",
                    "可以使用法宝、符箓、阵法",
                    "存在天劫、心魔等考验"
                ]
            },
            "western_fantasy": {
                "name": "西方奇幻",
                "description": "剑与魔法的奇幻世界，有精灵、矮人、巨龙等种族",
                "genre": "西方奇幻",
                "rules": [
                    "存在魔法师、战士、盗贼等职业",
                    "有精灵、矮人、兽人等不同种族",
                    "可以使用魔法和锻造武器",
                    "存在中世纪风格的王国和城邦"
                ]
            },
            "modern_city": {
                "name": "现代都市",
                "description": "现代都市背景，讲述职场、爱情、悬疑等故事",
                "genre": "现代都市",
                "rules": [
                    "背景设定在现代城市",
                    "可以涉及职场、情感、悬疑等题材",
                    "人物有现代社会的身份和职业",
                    "符合现代社会的基本常识"
                ]
            },
            "historical": {
                "name": "历史架空",
                "description": "基于历史或架空历史的背景设定",
                "genre": "历史架空",
                "rules": [
                    "可以基于真实历史时期",
                    "也可以是完全架空的历史",
                    "需要符合当时的社会背景",
                    "可以有宫廷、江湖、战争等元素"
                ]
            },
            "sci_fi": {
                "name": "科幻未来",
                "description": "未来科幻世界，有星际旅行、人工智能、外星文明等",
                "genre": "科幻",
                "rules": [
                    "设定在未来或太空",
                    "可以有高科技、星际旅行、人工智能",
                    "可以涉及外星文明和宇宙探索",
                    "需要有一定的科学依据或自洽的设定"
                ]
            },
            "horror": {
                "name": "悬疑恐怖",
                "description": "悬疑、惊悚、恐怖题材的世界观设定",
                "genre": "悬疑恐怖",
                "rules": [
                    "营造紧张恐怖的氛围",
                    "可以有超自然现象或心理恐怖",
                    "悬念迭起，出人意料",
                    "探索人性的黑暗面"
                ]
            }
        }

    def create_session(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        initial_text: Optional[str] = None,
        style_id: Optional[str] = None,
        world_setting_id: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = f"col_{uuid.uuid4().hex[:8]}"
        
        session = CollabWritingSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            description=description
        )

        if initial_text:
            session.add_segment(
                content=initial_text,
                writer="用户",
                writer_type=WriterType.USER.value
            )

        if style_id and style_id in self.preset_styles:
            session.selected_style = self.preset_styles[style_id]

        if world_setting_id and world_setting_id in self.preset_world_settings:
            ws = self.preset_world_settings[world_setting_id]
            session.add_world_setting(
                name=ws["name"],
                description=ws["description"],
                genre=ws.get("genre"),
                rules=ws.get("rules", [])
            )

        self._save_session(session)

        return {
            "success": True,
            "data": self._session_to_response(session)
        }

    def get_session(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._load_session(user_id, session_id)
        if not session:
            return None
        return {
            "success": True,
            "data": self._session_to_response(session)
        }

    def list_sessions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        user_path = self._get_user_sessions_path(user_id)
        
        sessions = []
        for sess_file in user_path.glob("col_*.json"):
            try:
                data = json.loads(sess_file.read_text())
                session = CollabWritingSession.from_dict(data)
                sessions.append(session)
            except Exception:
                continue

        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        total = len(sessions)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated = sessions[start:end]

        return {
            "success": True,
            "data": {
                "sessions": [self._session_to_response(s, include_segments=False) for s in paginated],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }

    def user_write(
        self,
        user_id: str,
        session_id: str,
        content: str
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        if session.is_alternating and session.last_writer == WriterType.USER.value:
            return {
                "success": False,
                "error": "请等待AI回复后再继续"
            }

        if not content or not content.strip():
            return {
                "success": False,
                "error": "内容不能为空"
            }

        segment = session.add_segment(
            content=content.strip(),
            writer="用户",
            writer_type=WriterType.USER.value
        )

        self._save_session(session)

        return {
            "success": True,
            "data": {
                "segment": segment.to_dict(),
                "session": self._session_to_response(session)
            }
        }

    async def ai_continue(
        self,
        user_id: str,
        session_id: str,
        volcengine_service: VolcEngineService,
        branch_count: int = 3
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        if session.is_alternating and session.last_writer == WriterType.AI.value:
            return {
                "success": False,
                "error": "请等待用户回复后再继续"
            }

        branches = []
        
        for i in range(branch_count):
            branch_content = await self._generate_ai_continuation(
                session, volcengine_service, i, branch_count
            )
            
            if branch_content:
                branch = session.add_branch(
                    parent_segment_id=session.segments[-1].segment_id if session.segments else "",
                    content=branch_content,
                    description=f"分支选项 {i + 1}"
                )
                branches.append(branch)

        self._save_session(session)

        return {
            "success": True,
            "data": {
                "branches": [b.to_dict() for b in branches],
                "session": self._session_to_response(session)
            }
        }

    async def _generate_ai_continuation(
        self,
        session: CollabWritingSession,
        volcengine_service: VolcEngineService,
        branch_index: int,
        total_branches: int
    ) -> Optional[str]:
        context = session.get_context_for_ai()
        
        style_prompt = ""
        if session.selected_style:
            style_prompt = f"\n\n写作风格要求：{session.selected_style.prompt_template}"
        
        branch_variation = ""
        if total_branches > 1:
            variations = [
                "请尝试一个更加戏剧性的发展方向。",
                "请尝试一个更加温馨感人的发展方向。",
                "请尝试一个更加出人意料的发展方向。",
                "请尝试一个更加紧张刺激的发展方向。",
                "请尝试一个更加诗意浪漫的发展方向。"
            ]
            branch_variation = variations[branch_index % len(variations)]
        
        system_prompt = f"""你是一个专业的写作助手，正在与用户进行协作创作。

你的任务是：
1. 仔细阅读之前的上下文
2. 理解故事的节奏和走向
3. 续写一段自然流畅的内容
4. 保持与前文的连贯性
5. 续写长度适中，约100-300字{style_prompt}

{branch_variation}

注意：
- 只返回续写的内容本身，不要包含其他解释
- 保持与用户相同的语言风格
- 不要重复前文内容
- 给用户留出继续创作的空间"""

        user_prompt = f"""以下是当前创作的上下文：

{context}

请续写一段内容："""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]

        temperature = 0.7 + (branch_index * 0.15)
        result = volcengine_service.chat_completion(
            messages,
            temperature=min(temperature, 1.0),
            max_tokens=500
        )

        if result.success and result.content:
            return result.content.strip()
        
        return None

    def select_branch(
        self,
        user_id: str,
        session_id: str,
        branch_id: str
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        segment = session.select_branch(branch_id)
        
        if segment:
            self._save_session(session)
            return {
                "success": True,
                "data": {
                    "selected_segment": segment.to_dict(),
                    "session": self._session_to_response(session)
                }
            }
        else:
            return {
                "success": False,
                "error": "分支选择失败"
            }

    def set_writing_style(
        self,
        user_id: str,
        session_id: str,
        style_id: str
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        if style_id not in self.preset_styles:
            return {
                "success": False,
                "error": "写作风格不存在"
            }

        session.selected_style = self.preset_styles[style_id]
        session.updated_at = datetime.now().isoformat()
        self._save_session(session)

        return {
            "success": True,
            "data": {
                "selected_style": session.selected_style.to_dict(),
                "session": self._session_to_response(session)
            }
        }

    def add_character(
        self,
        user_id: str,
        session_id: str,
        name: str,
        description: str,
        personality: Optional[str] = None,
        background: Optional[str] = None,
        traits: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        character = session.add_character(
            name=name,
            description=description,
            personality=personality,
            background=background,
            traits=traits
        )

        self._save_session(session)

        return {
            "success": True,
            "data": {
                "character": character.to_dict(),
                "session": self._session_to_response(session)
            }
        }

    def add_world_setting(
        self,
        user_id: str,
        session_id: str,
        name: str,
        description: str,
        genre: Optional[str] = None,
        era: Optional[str] = None,
        rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        session = self._load_session(user_id, session_id)
        if not session:
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        setting = session.add_world_setting(
            name=name,
            description=description,
            genre=genre,
            era=era,
            rules=rules
        )

        self._save_session(session)

        return {
            "success": True,
            "data": {
                "world_setting": setting.to_dict(),
                "session": self._session_to_response(session)
            }
        }

    def get_preset_styles(self) -> Dict[str, Any]:
        return {
            "success": True,
            "data": {
                "styles": [
                    {
                        "style_id": style.style_id,
                        "name": style.name,
                        "type": style.type,
                        "description": style.description
                    }
                    for style in self.preset_styles.values()
                ]
            }
        }

    def get_preset_world_settings(self) -> Dict[str, Any]:
        return {
            "success": True,
            "data": {
                "world_settings": [
                    {
                        "setting_id": key,
                        "name": value["name"],
                        "description": value["description"],
                        "genre": value.get("genre")
                    }
                    for key, value in self.preset_world_settings.items()
                ]
            }
        }

    def delete_session(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        user_path = self._get_user_sessions_path(user_id)
        sess_file = user_path / f"{session_id}.json"
        
        if not sess_file.exists():
            return {
                "success": False,
                "error": "协作会话不存在"
            }

        try:
            sess_file.unlink()
            return {
                "success": True,
                "message": "协作会话已删除"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除协作会话失败: {str(e)}"
            }

    def _get_user_sessions_path(self, user_id: str) -> Path:
        user_path = self.sessions_dir / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path

    def _load_session(self, user_id: str, session_id: str) -> Optional[CollabWritingSession]:
        user_path = self._get_user_sessions_path(user_id)
        sess_file = user_path / f"{session_id}.json"
        
        if not sess_file.exists():
            return None

        try:
            data = json.loads(sess_file.read_text())
            return CollabWritingSession.from_dict(data)
        except Exception:
            return None

    def _save_session(self, session: CollabWritingSession):
        user_path = self._get_user_sessions_path(session.user_id)
        sess_file = user_path / f"{session.session_id}.json"
        
        with open(sess_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def _session_to_response(self, session: CollabWritingSession, include_segments: bool = True) -> Dict[str, Any]:
        response = {
            "session_id": session.session_id,
            "title": session.title,
            "description": session.description,
            "turn_count": session.turn_count,
            "last_writer": session.last_writer,
            "is_alternating": session.is_alternating,
            "segment_count": len(session.segments),
            "character_count": len(session.characters),
            "world_setting_count": len(session.world_settings),
            "selected_style": session.selected_style.to_dict() if session.selected_style else None,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }

        if include_segments:
            response["segments"] = [s.to_dict() for s in session.segments]
            response["branches"] = [b.to_dict() for b in session.branches]
            response["characters"] = [c.to_dict() for c in session.characters]
            response["world_settings"] = [w.to_dict() for w in session.world_settings]

        return response

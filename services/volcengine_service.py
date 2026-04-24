import json
import base64
import uuid
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from config import get_settings, IMAGE_STYLES


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ImageGenerationResult:
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    revised_prompt: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ChatResult:
    success: bool
    content: Optional[str] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None


@dataclass
class TTSResult:
    success: bool
    audio_data: Optional[bytes] = None
    duration: Optional[float] = None
    error: Optional[str] = None


class VolcEngineService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        image_model: Optional[str] = None,
        tts_appid: Optional[str] = None,
        tts_token: Optional[str] = None
    ):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.VOLCENGINE_API_KEY
        self.chat_model = chat_model or self.settings.VOLCENGINE_CHAT_MODEL
        self.image_model = image_model or self.settings.VOLCENGINE_IMAGE_MODEL
        self.tts_appid = tts_appid or self.settings.VOLCENGINE_TTS_APPID
        self.tts_token = tts_token or self.settings.VOLCENGINE_TTS_ACCESS_TOKEN
        
        self.chat_url = self.settings.VOLCENGINE_CHAT_URL
        self.image_url = self.settings.VOLCENGINE_IMAGE_URL
        self.tts_url = self.settings.VOLCENGINE_TTS_URL

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        headers = {
            "Content-Type": content_type,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> ChatResult:
        if not self.api_key:
            return ChatResult(
                success=False,
                error="API Key 未配置，请在前端配置 VOLCENGINE_API_KEY"
            )

        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.chat_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return ChatResult(
                            success=False,
                            error=f"API请求失败: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        content = choice.get("message", {}).get("content", "")
                        usage = data.get("usage", {})
                        model = data.get("model", self.chat_model)
                        
                        return ChatResult(
                            success=True,
                            content=content,
                            model=model,
                            usage=usage
                        )
                    else:
                        return ChatResult(
                            success=False,
                            error=f"API返回格式异常: {json.dumps(data)}"
                        )
                        
        except asyncio.TimeoutError:
            return ChatResult(
                success=False,
                error="请求超时，请稍后重试"
            )
        except Exception as e:
            return ChatResult(
                success=False,
                error=f"请求异常: {str(e)}"
            )

    async def generate_image_prompt(self, text: str, style: str = "cartoon") -> str:
        style_config = IMAGE_STYLES.get(style, IMAGE_STYLES["cartoon"])
        
        system_prompt = """你是一个专业的图像提示词生成专家，专门为记忆卡片生成适合的图像描述。
你的任务是：
1. 理解输入文本的核心含义和情感
2. 生成一个生动、具体、适合AI绘画的图像提示词
3. 提示词应该包含：场景描述、主体特征、光影效果、色彩风格、构图方式
4. 提示词要适合青少年学习使用，积极向上，色彩鲜明

注意：
- 只返回图像提示词本身，不要包含其他解释
- 提示词要具体，避免抽象概念
- 要适合生成记忆锚点图片，帮助记忆"""

        user_prompt = f"""请为以下文本生成一个图像提示词，用于制作记忆卡片：

文本内容：{text}

风格要求：{style_config['description']}

请直接返回图像提示词（中文）："""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]
        
        result = await self.chat_completion(messages, temperature=0.8, max_tokens=500)
        
        if result.success and result.content:
            return f"{style_config['prompt_prefix']}{result.content}{style_config['suffix']}"
        else:
            return f"{style_config['prompt_prefix']}{text}{style_config['suffix']}"

    async def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        n: int = 1
    ) -> ImageGenerationResult:
        if not self.api_key:
            return ImageGenerationResult(
                success=False,
                error="API Key 未配置，请在前端配置 VOLCENGINE_API_KEY"
            )

        size = size or self.settings.IMAGE_SIZE
        quality = quality or self.settings.IMAGE_QUALITY

        payload = {
            "model": self.image_model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
            "response_format": "b64_json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.image_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return ImageGenerationResult(
                            success=False,
                            error=f"图像生成API请求失败: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    
                    if "data" in data and len(data["data"]) > 0:
                        image_data = data["data"][0]
                        image_base64 = image_data.get("b64_json")
                        revised_prompt = image_data.get("revised_prompt", prompt)
                        
                        return ImageGenerationResult(
                            success=True,
                            image_base64=image_base64,
                            revised_prompt=revised_prompt
                        )
                    else:
                        return ImageGenerationResult(
                            success=False,
                            error=f"图像生成API返回格式异常: {json.dumps(data)}"
                        )
                        
        except asyncio.TimeoutError:
            return ImageGenerationResult(
                success=False,
                error="图像生成请求超时，请稍后重试"
            )
        except Exception as e:
            return ImageGenerationResult(
                success=False,
                error=f"图像生成请求异常: {str(e)}"
            )

    async def generate_tts(
        self,
        text: str,
        voice_type: str = "zh_female_shuangkuaisisi_moon_bigtts",
        speed: float = 1.0,
        pitch: float = 1.0,
        volume: float = 1.0
    ) -> TTSResult:
        if not self.tts_appid or not self.tts_token:
            return TTSResult(
                success=False,
                error="TTS配置未完成，请配置 VOLCENGINE_TTS_APPID 和 VOLCENGINE_TTS_ACCESS_TOKEN"
            )

        try:
            request_id = str(uuid.uuid4())
            
            payload = {
                "app": {
                    "appid": self.tts_appid,
                    "token": "access_token",
                    "cluster": "volcano_tts"
                },
                "user": {
                    "uid": "wordvivid_user"
                },
                "audio": {
                    "voice_type": voice_type,
                    "encoding": "mp3",
                    "speed_ratio": speed,
                    "volume_ratio": volume,
                    "pitch_ratio": pitch
                },
                "request": {
                    "reqid": request_id,
                    "text": text,
                    "text_type": "plain",
                    "operation": "query"
                }
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer;{self.tts_token}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tts_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return TTSResult(
                            success=False,
                            error=f"TTS API请求失败: {response.status} - {error_text}"
                        )
                    
                    data = await response.json()
                    
                    if data.get("code") == 3000 and "data" in data:
                        audio_base64 = data["data"]
                        audio_bytes = base64.b64decode(audio_base64)
                        
                        duration = data.get("duration", 0)
                        
                        return TTSResult(
                            success=True,
                            audio_data=audio_bytes,
                            duration=duration
                        )
                    else:
                        error_msg = data.get("message", "未知错误")
                        return TTSResult(
                            success=False,
                            error=f"TTS生成失败: {error_msg}"
                        )
                        
        except asyncio.TimeoutError:
            return TTSResult(
                success=False,
                error="TTS请求超时，请稍后重试"
            )
        except Exception as e:
            return TTSResult(
                success=False,
                error=f"TTS请求异常: {str(e)}"
            )

    async def split_text_smart(self, text: str, split_mode: str = "sentence") -> List[Dict[str, Any]]:
        system_prompt = """你是一个文本分割专家，专门为背诵记忆卡片进行文本分割。

分割原则：
1. 按语义完整性分割，确保每个片段都有完整的意义
2. 每段长度适中，适合单独记忆（建议10-50字）
3. 保留原文的标点符号和格式
4. 对于诗歌、古文等，按句或联分割
5. 对于现代文，按句子或完整意群分割

返回格式（JSON数组）：
[
    {"index": 0, "text": "第一段文本内容"},
    {"index": 1, "text": "第二段文本内容"}
]

只返回JSON数组，不要包含其他内容。"""

        user_prompt = f"""请将以下文本按{split_mode}模式分割：

分割模式说明：
- sentence: 按句子分割
- paragraph: 按段落分割
- auto: 智能自动分割（根据文本类型选择最合适的方式）

文本内容：
{text}

请返回分割后的JSON数组："""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]

        result = await self.chat_completion(messages, temperature=0.3, max_tokens=4000)

        if result.success and result.content:
            try:
                segments = json.loads(result.content)
                return [
                    {
                        "id": f"seg_{str(i).zfill(3)}",
                        "text": seg.get("text", ""),
                        "index": seg.get("index", i)
                    }
                    for i, seg in enumerate(segments)
                ]
            except json.JSONDecodeError:
                pass
        
        return self._fallback_split(text, split_mode)

    def _fallback_split(self, text: str, split_mode: str) -> List[Dict[str, Any]]:
        import re
        
        if split_mode == "paragraph":
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            return [
                {"id": f"seg_{str(i).zfill(3)}", "text": p, "index": i}
                for i, p in enumerate(paragraphs)
            ]
        else:
            sentence_endings = r'[。！？.!?]+'
            sentences = re.split(f'({sentence_endings})', text)
            
            result = []
            current = ""
            index = 0
            
            for i in range(0, len(sentences), 2):
                part = sentences[i]
                punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
                
                if part.strip() or punctuation:
                    full_sentence = f"{part}{punctuation}".strip()
                    if full_sentence:
                        result.append({
                            "id": f"seg_{str(index).zfill(3)}",
                            "text": full_sentence,
                            "index": index
                        })
                        index += 1
            
            return result if result else [{"id": "seg_000", "text": text, "index": 0}]

    async def calculate_similarity(self, text1: str, text2: str) -> float:
        system_prompt = """你是一个文本相似度评估专家。请评估两个文本之间的语义相似度，返回0到1之间的浮点数。

评估标准：
- 1.0: 完全相同或意思完全一致
- 0.8-0.99: 意思非常接近，只有细微差别
- 0.5-0.79: 意思部分相同，有一些差异
- 0.3-0.49: 意思不太相同，只有部分关联
- 0-0.29: 意思基本不同或完全无关

只返回一个数字，不要包含其他内容。"""

        user_prompt = f"""请评估以下两个文本的语义相似度：

文本1：{text1}
文本2：{text2}

返回相似度分数（0-1之间的浮点数）："""

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]

        result = await self.chat_completion(messages, temperature=0.1, max_tokens=10)

        if result.success and result.content:
            try:
                similarity = float(result.content.strip())
                return max(0.0, min(1.0, similarity))
            except ValueError:
                pass
        
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()

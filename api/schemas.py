from typing import Optional, List
from pydantic import BaseModel, Field


class ProcessTextRequest(BaseModel):
    text: str = Field(..., description="需要处理的文本内容")
    split_mode: str = Field(default="sentence", description="分割模式: sentence/paragraph/auto")
    api_key: Optional[str] = Field(default=None, description="火山引擎API Key")
    chat_model: Optional[str] = Field(default=None, description="对话模型名称")


class GenerateCardRequest(BaseModel):
    text: str = Field(..., description="卡片文本内容")
    original_text: Optional[str] = Field(default=None, description="原始完整文本")
    segment_index: int = Field(default=0, description="片段索引")
    user_id: str = Field(default="default_user", description="用户ID")
    style: str = Field(default="cartoon", description="图像风格: cartoon/anime/realistic/watercolor/pixel/3d")
    voice_type: str = Field(default="zh_female_shuangkuaisisi_moon_bigtts", description="语音音色")
    generate_image: bool = Field(default=True, description="是否生成图像")
    generate_audio: bool = Field(default=True, description="是否生成语音")
    api_key: Optional[str] = Field(default=None, description="火山引擎API Key")
    chat_model: Optional[str] = Field(default=None, description="对话模型名称")
    image_model: Optional[str] = Field(default=None, description="图像生成模型名称")
    tts_appid: Optional[str] = Field(default=None, description="TTS AppID")
    tts_token: Optional[str] = Field(default=None, description="TTS AccessToken")


class GenerateCardsBatchRequest(BaseModel):
    segments: List[dict] = Field(..., description="文本片段列表")
    original_text: Optional[str] = Field(default=None, description="原始完整文本")
    user_id: str = Field(default="default_user", description="用户ID")
    style: str = Field(default="cartoon", description="图像风格")
    voice_type: str = Field(default="zh_female_shuangkuaisisi_moon_bigtts", description="语音音色")
    generate_image: bool = Field(default=True, description="是否生成图像")
    generate_audio: bool = Field(default=True, description="是否生成语音")
    api_key: Optional[str] = Field(default=None, description="火山引擎API Key")
    chat_model: Optional[str] = Field(default=None, description="对话模型名称")
    image_model: Optional[str] = Field(default=None, description="图像生成模型名称")


class UpdateCardRequest(BaseModel):
    category: Optional[str] = Field(default=None, description="分类")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class StartGameRequest(BaseModel):
    user_id: str = Field(default="default_user", description="用户ID")
    game_type: str = Field(default="image_to_text", description="游戏类型: image_to_text/audio_to_text/mixed")
    card_ids: Optional[List[str]] = Field(default=None, description="指定卡片ID列表")
    card_count: int = Field(default=10, description="卡片数量")
    shuffle: bool = Field(default=True, description="是否随机打乱")


class SubmitAnswerRequest(BaseModel):
    game_id: str = Field(..., description="游戏会话ID")
    card_id: str = Field(..., description="卡片ID")
    user_answer: str = Field(..., description="用户答案")
    similarity_threshold: float = Field(default=0.7, description="相似度阈值")


class ShareCardRequest(BaseModel):
    card_id: str = Field(..., description="卡片ID")
    user_id: str = Field(default="default_user", description="用户ID")
    title: str = Field(..., description="分享标题")
    description: str = Field(default="", description="分享描述")
    category: str = Field(default="default", description="分类")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class ApiResponse(BaseModel):
    success: bool = Field(default=True, description="是否成功")
    data: Optional[dict] = Field(default=None, description="数据内容")
    error: Optional[str] = Field(default=None, description="错误信息")
    message: Optional[str] = Field(default=None, description="提示信息")

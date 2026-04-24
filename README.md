# WordVivid - AI多模态背诵辅助工具

<div align="center">

🎨 **让背诵变得有趣、高效、多感官** ✨

</div>

---

## 🌟 项目简介

WordVivid 是一款面向青少年的AI多模态背诵辅助工具。它将枯燥的文字一键转化为**图文并茂、有声有色**的创意记忆卡片，让背诵变得高效且有趣！

### 🎯 核心功能

| 功能模块 | 描述 |
|---------|------|
| **📝 文本输入** | 支持手动输入或OCR拍照识别文本 |
| **✂️ 智能分割** | 自动按句段分割文本，方便逐句记忆 |
| **🖼️ AI插图生成** | 为每段文本生成高度相关的记忆锚点插图 |
| **🎵 AI语音合成** | 生成多音色、带配乐的生动语音 |
| **📦 个人记忆库** | 支持分类管理，快速检索复习 |
| **🎮 自测游戏** | 看图猜文、听音辨文的翻转卡片游戏 |
| **🌐 公共画廊** | 分享交流，发现他人的创意记忆卡片 |

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip 或 poetry

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd WordVivid
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置火山引擎API**

在使用前，需要在前端界面配置以下信息（或通过环境变量配置）：

| 配置项 | 说明 |
|-------|------|
| `VOLCENGINE_API_KEY` | 火山引擎API Key |
| `VOLCENGINE_CHAT_MODEL` | 对话模型名称（如：doubao-seed-1.8） |
| `VOLCENGINE_IMAGE_MODEL` | 图像生成模型名称（如：doubao-seedream-5.0-lite） |
| `VOLCENGINE_TTS_APPID` | 语音合成AppID |
| `VOLCENGINE_TTS_ACCESS_TOKEN` | 语音合成AccessToken |

> 💡 **如何获取API Key？**
> 1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
> 2. 开通「火山方舟」服务
> 3. 在「API Key管理」中创建并获取API Key
> 4. 在「模型推理接入点」中查看可使用的模型名称

4. **启动服务**

```bash
python app.py
```

服务将在 **http://localhost:9652** 启动

---

## 📁 项目结构

```
WordVivid/
├── app.py                    # 主应用入口
├── config.py                 # 配置管理
├── requirements.txt          # Python依赖
├── README.md                # 项目文档
│
├── api/                      # API模块
│   ├── __init__.py
│   ├── routes.py            # API路由定义
│   └── schemas.py           # 请求/响应数据模型
│
├── services/                 # 业务服务层
│   ├── __init__.py
│   ├── volcengine_service.py  # 火山引擎API服务
│   ├── card_generator.py       # 记忆卡片生成服务
│   ├── memory_library.py       # 记忆库管理服务
│   ├── game_service.py         # 自测游戏服务
│   └── gallery_service.py      # 公共画廊服务
│
├── models/                    # 数据模型
│   ├── __init__.py
│   ├── card.py               # 记忆卡片模型
│   └── user.py               # 用户模型
│
├── utils/                     # 工具函数
│   ├── __init__.py
│   ├── text_processor.py     # 文本处理工具
│   └── validator.py          # 数据验证工具
│
├── static/                    # 静态文件
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                 # HTML模板
│   └── index.html
│
└── data/                      # 数据存储
    ├── cards/                 # 生成的卡片数据
    ├── images/                # 生成的图片
    └── audio/                 # 生成的音频
```

---

## 🔌 API接口文档

### 基础URL

```
http://localhost:9652/api
```

### 认证

所有需要调用火山引擎API的接口，都需要在请求头中携带配置信息：

```json
{
  "X-Volcengine-Api-Key": "your-api-key",
  "X-Volcengine-Chat-Model": "doubao-seed-1.8",
  "X-Volcengine-Image-Model": "doubao-seedream-5.0-lite"
}
```

### 接口列表

#### 1. 文本处理与分割

**POST** `/text/process`

将输入文本按句段智能分割。

**请求体：**
```json
{
  "text": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
  "split_mode": "sentence"  // sentence: 按句子, paragraph: 按段落
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "segments": [
      {
        "id": "seg_001",
        "text": "床前明月光，疑是地上霜。",
        "index": 0
      },
      {
        "id": "seg_002",
        "text": "举头望明月，低头思故乡。",
        "index": 1
      }
    ]
  }
}
```

#### 2. 生成记忆卡片

**POST** `/cards/generate`

为文本片段生成包含插图和语音的记忆卡片。

**请求体：**
```json
{
  "text": "床前明月光，疑是地上霜。",
  "style": "cartoon",  // cartoon: 卡通风格, realistic: 写实风格, anime: 动漫风格
  "voice_type": "zh_female_shuangkuaisisi_moon_bigtts",  // 语音音色
  "generate_image": true,
  "generate_audio": true
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "card_id": "card_abc123",
    "text": "床前明月光，疑是地上霜。",
    "image_url": "/data/images/card_abc123.png",
    "audio_url": "/data/audio/card_abc123.mp3",
    "style": "cartoon",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 3. 保存卡片到记忆库

**POST** `/library/save`

将生成的卡片保存到个人记忆库。

**请求体：**
```json
{
  "card_id": "card_abc123",
  "user_id": "user_001",
  "category": "古诗词",
  "tags": ["唐诗", "李白", "静夜思"]
}
```

#### 4. 获取记忆库列表

**GET** `/library/list`

**查询参数：**
- `user_id`: 用户ID
- `category`: 分类筛选（可选）
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）

#### 5. 开始自测游戏

**POST** `/game/start`

开始翻转卡片自测游戏。

**请求体：**
```json
{
  "user_id": "user_001",
  "game_type": "image_to_text",  // image_to_text: 看图猜文, audio_to_text: 听音辨文
  "card_ids": ["card_abc123", "card_def456"]  // 可选，不指定则随机选择
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "game_id": "game_xyz789",
    "total_cards": 10,
    "current_index": 0,
    "current_card": {
      "card_id": "card_abc123",
      "image_url": "/data/images/card_abc123.png",
      "audio_url": "/data/audio/card_abc123.mp3"
    }
  }
}
```

#### 6. 提交游戏答案

**POST** `/game/submit`

```json
{
  "game_id": "game_xyz789",
  "card_id": "card_abc123",
  "user_answer": "床前明月光",
  "answer_type": "text"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "is_correct": true,
    "correct_answer": "床前明月光，疑是地上霜。",
    "similarity": 0.85,
    "next_card": {
      "card_id": "card_def456",
      "image_url": "/data/images/card_def456.png"
    }
  }
}
```

#### 7. 获取公共画廊

**GET** `/gallery/list`

获取社区分享的记忆卡片。

**查询参数：**
- `sort`: 排序方式（hot, new）
- `category`: 分类筛选
- `page`: 页码

#### 8. 分享卡片到画廊

**POST** `/gallery/share`

```json
{
  "card_id": "card_abc123",
  "user_id": "user_001",
  "title": "静夜思 - 创意记忆卡片",
  "description": "用卡通风格呈现的李白《静夜思》，帮助快速记忆"
}
```

---

## 🎨 配置说明

### 支持的图像风格

| 风格名称 | 说明 |
|---------|------|
| `cartoon` | 卡通风格 - 适合儿童青少年，色彩鲜艳 |
| `anime` | 动漫风格 - 日系动漫风格 |
| `realistic` | 写实风格 - 照片级真实感 |
| `watercolor` | 水彩风格 - 艺术水彩效果 |
| `pixel` | 像素风格 - 复古游戏风格 |
| `3d` | 3D风格 - 三维渲染效果 |

### 支持的语音音色

火山引擎提供丰富的音色选择，常用音色包括：

| 音色ID | 说明 |
|--------|------|
| `zh_female_shuangkuaisisi_moon_bigtts` | 女声 - 活泼甜美 |
| `zh_male_chunhou_chaoren_bigtts` | 男声 - 沉稳磁性 |
| `zh_female_wanrou_lingwei_bigtts` | 女声 - 温柔亲切 |
| `zh_male_novel_yechen_bigtts` | 男声 - 故事讲述 |
| `zh_female_child_xiaoyue_bigtts` | 童声 - 小女孩 |
| `zh_male_child_doubao_bigtts` | 童声 - 小男孩 |

> 完整音色列表请参考 [火山引擎语音合成文档](https://www.volcengine.com/docs/6561/1096680)

---

## 🔧 火山引擎API接入详情

### 对话API (Chat Completions)

**端点：** `POST https://ark.cn-beijing.volces.com/api/v3/chat/completions`

**认证方式：** Bearer Token (API Key)

**使用场景：**
- 文本理解与智能分割
- 生成图像提示词（Image Prompt）
- 答案相似度评估

**请求示例：**
```python
import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": model_name,
    "messages": [
        {"role": "user", "content": "请为以下文本生成一个适合的图像提示词：床前明月光"}
    ]
}

response = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    headers=headers,
    json=payload
)
```

### 图像生成API (Image Generations)

**端点：** `POST https://ark.cn-beijing.volces.com/api/v3/images/generations`

**认证方式：** Bearer Token (API Key)

**使用场景：**
- 为文本片段生成记忆锚点插图

**支持的模型：**
- `doubao-seedream-5.0-lite`
- `doubao-seedream-4.5`
- `doubao-seedream-4.0`

**支持的尺寸：**
- 2K分辨率：2048x2048, 2304x1728, 2848x1600 等
- 4K分辨率：4096x4096, 4704x3520, 5504x3040 等

**请求示例：**
```python
import requests

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "model": "doubao-seedream-5.0-lite",
    "prompt": "一个卡通风格的夜晚场景，明亮的月亮照在床前，地上仿佛有一层白霜",
    "size": "2048x2048",
    "quality": "standard",
    "n": 1
}

response = requests.post(
    "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    headers=headers,
    json=payload
)
```

### 语音合成API (TTS)

**端点：** 根据具体服务而定

**认证方式：** AppID + AccessToken

**使用场景：**
- 将文本转换为生动的语音
- 支持多音色、多风格

---

## 📊 数据存储

### 本地存储结构

```
data/
├── cards/
│   └── {user_id}/
│       └── {card_id}.json
├── images/
│   └── {card_id}.png
├── audio/
│   └── {card_id}.mp3
└── gallery/
    └── shared_cards.json
```

### 卡片数据结构

```json
{
  "card_id": "card_abc123",
  "user_id": "user_001",
  "text": "床前明月光，疑是地上霜。",
  "original_text": "完整原文...",
  "segment_index": 0,
  "image": {
    "url": "/data/images/card_abc123.png",
    "style": "cartoon",
    "prompt": "生成的图像提示词"
  },
  "audio": {
    "url": "/data/audio/card_abc123.mp3",
    "voice_type": "zh_female_shuangkuaisisi_moon_bigtts",
    "duration": 5.2
  },
  "metadata": {
    "category": "古诗词",
    "tags": ["唐诗", "李白"],
    "created_at": "2024-01-15T10:30:00Z",
    "review_count": 15,
    "correct_rate": 0.85
  }
}
```

---

## 🛠️ 开发指南

### 添加新的图像风格

1. 在 `config.py` 中添加风格配置：
```python
IMAGE_STYLES = {
    "your_new_style": {
        "description": "风格描述",
        "prompt_prefix": "风格前缀提示词",
        "suffix": "风格后缀提示词"
    }
}
```

### 自定义文本分割逻辑

修改 `utils/text_processor.py` 中的 `split_text` 函数。

### 扩展游戏模式

在 `services/game_service.py` 中添加新的游戏类型。

---

## 🚀 部署说明

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务（端口9652）
python app.py
```

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9652

CMD ["python", "app.py"]
```

```bash
# 构建并运行
docker build -t wordvivid .
docker run -p 9652:9652 wordvivid
```

---

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- ✨ 支持文本输入与智能分割
- ✨ 集成火山引擎对话API
- ✨ 集成火山引擎图像生成API
- ✨ 集成火山引擎语音合成API
- ✨ 个人记忆库管理功能
- ✨ 翻转卡片自测游戏
- ✨ 公共记忆画廊

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系方式

- 项目地址：[GitHub Repository]
- 问题反馈：[Issues]
- 文档：[Wiki]

---

<div align="center">

**用AI点亮记忆，让背诵成为乐趣！** 🎉

</div>

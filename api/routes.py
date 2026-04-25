from flask import Blueprint, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import uuid
import asyncio

from config import get_settings, IMAGE_STYLES, VOICE_TYPES
from services.volcengine_service import VolcEngineService
from services.card_generator import CardGeneratorService
from services.memory_library import MemoryLibraryService
from services.game_service import GameService
from services.gallery_service import GalleryService
from services.storyline_service import StorylineService
from services.collab_writing_service import CollabWritingService
from services.vivid_mirror_service import VividMirrorService
from api.schemas import (
    ProcessTextRequest,
    GenerateCardRequest,
    GenerateCardsBatchRequest,
    UpdateCardRequest,
    StartGameRequest,
    SubmitAnswerRequest,
    ShareCardRequest
)


api_bp = Blueprint('api', __name__)
CORS(api_bp)

settings = get_settings()


def _get_volcengine_service(headers: dict, body: dict = None) -> VolcEngineService:
    api_key = headers.get('X-Volcengine-Api-Key') or (body.get('api_key') if body else None)
    chat_model = headers.get('X-Volcengine-Chat-Model') or (body.get('chat_model') if body else None)
    image_model = headers.get('X-Volcengine-Image-Model') or (body.get('image_model') if body else None)
    tts_appid = headers.get('X-Volcengine-Tts-Appid') or (body.get('tts_appid') if body else None)
    tts_token = headers.get('X-Volcengine-Tts-Token') or (body.get('tts_token') if body else None)
    
    return VolcEngineService(
        api_key=api_key,
        chat_model=chat_model,
        image_model=image_model,
        tts_appid=tts_appid,
        tts_token=tts_token
    )


@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION
        }
    })


@api_bp.route('/config/styles', methods=['GET'])
def get_styles():
    styles_list = [
        {"key": key, "description": value["description"]}
        for key, value in IMAGE_STYLES.items()
    ]
    return jsonify({
        "success": True,
        "data": {
            "styles": styles_list
        }
    })


@api_bp.route('/config/voices', methods=['GET'])
def get_voices():
    voices_list = [
        {"key": key, "description": value}
        for key, value in VOICE_TYPES.items()
    ]
    return jsonify({
        "success": True,
        "data": {
            "voices": voices_list
        }
    })


@api_bp.route('/text/process', methods=['POST'])
def process_text():
    try:
        data = request.get_json()
        text = data.get('text', '')
        split_mode = data.get('split_mode', 'sentence')
        
        if not text or not text.strip():
            return jsonify({
                "success": False,
                "error": "文本内容不能为空"
            }), 400

        volcengine = _get_volcengine_service(request.headers, data)
        segments = volcengine.split_text_smart(text, split_mode)

        return jsonify({
            "success": True,
            "data": {
                "segments": segments,
                "total_count": len(segments)
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/cards/generate', methods=['POST'])
def generate_card():
    try:
        data = request.get_json()
        
        text = data.get('text', '')
        if not text or not text.strip():
            return jsonify({
                "success": False,
                "error": "卡片文本不能为空"
            }), 400

        volcengine = _get_volcengine_service(request.headers, data)
        card_service = CardGeneratorService(volcengine)
        
        result = card_service.generate_card(
            user_id=data.get('user_id', 'default_user'),
            text=text,
            original_text=data.get('original_text'),
            segment_index=data.get('segment_index', 0),
            style=data.get('style', 'cartoon'),
            voice_type=data.get('voice_type', 'zh_female_shuangkuaisisi_moon_bigtts'),
            generate_image=data.get('generate_image', True),
            generate_audio=data.get('generate_audio', True),
            api_key=data.get('api_key'),
            chat_model=data.get('chat_model'),
            image_model=data.get('image_model')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/cards/generate-batch', methods=['POST'])
def generate_cards_batch():
    try:
        data = request.get_json()
        
        segments = data.get('segments', [])
        if not segments:
            return jsonify({
                "success": False,
                "error": "文本片段列表不能为空"
            }), 400

        volcengine = _get_volcengine_service(request.headers, data)
        card_service = CardGeneratorService(volcengine)
        
        result = card_service.generate_cards_batch(
            user_id=data.get('user_id', 'default_user'),
            segments=segments,
            original_text=data.get('original_text'),
            style=data.get('style', 'cartoon'),
            voice_type=data.get('voice_type', 'zh_female_shuangkuaisisi_moon_bigtts'),
            generate_image=data.get('generate_image', True),
            generate_audio=data.get('generate_audio', True),
            api_key=data.get('api_key'),
            chat_model=data.get('chat_model'),
            image_model=data.get('image_model')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/list', methods=['GET'])
def list_library():
    try:
        user_id = request.args.get('user_id', 'default_user')
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        library_service = MemoryLibraryService()
        result = library_service.list_cards(
            user_id=user_id,
            category=category,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/<card_id>', methods=['GET'])
def get_library_card(card_id):
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        library_service = MemoryLibraryService()
        card = library_service.get_card(user_id, card_id)
        
        if not card:
            return jsonify({
                "success": False,
                "error": "卡片不存在"
            }), 404

        return jsonify({
            "success": True,
            "data": card
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/<card_id>', methods=['PUT'])
def update_library_card(card_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        library_service = MemoryLibraryService()
        result = library_service.update_card(
            user_id=user_id,
            card_id=card_id,
            category=data.get('category'),
            tags=data.get('tags')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/<card_id>', methods=['DELETE'])
def delete_library_card(card_id):
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        library_service = MemoryLibraryService()
        result = library_service.delete_card(user_id, card_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/stats', methods=['GET'])
def get_library_stats():
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        library_service = MemoryLibraryService()
        result = library_service.get_stats(user_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/library/categories', methods=['GET'])
def get_library_categories():
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        library_service = MemoryLibraryService()
        result = library_service.get_categories(user_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/game/start', methods=['POST'])
def start_game():
    try:
        data = request.get_json()
        
        game_service = GameService()
        result = game_service.start_game(
            user_id=data.get('user_id', 'default_user'),
            game_type=data.get('game_type', 'image_to_text'),
            card_ids=data.get('card_ids'),
            card_count=data.get('card_count', 10),
            shuffle=data.get('shuffle', True)
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/game/<game_id>', methods=['GET'])
def get_game_status(game_id):
    try:
        game_service = GameService()
        result = game_service.get_current_card(game_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/game/submit', methods=['POST'])
def submit_answer():
    try:
        data = request.get_json()
        
        game_id = data.get('game_id')
        if not game_id:
            return jsonify({
                "success": False,
                "error": "游戏ID不能为空"
            }), 400

        volcengine = _get_volcengine_service(request.headers, data)
        game_service = GameService(volcengine)
        
        result = game_service.submit_answer(
            game_id=game_id,
            card_id=data.get('card_id', ''),
            user_answer=data.get('user_answer', ''),
            similarity_threshold=data.get('similarity_threshold', 0.7)
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/game/<game_id>/results', methods=['GET'])
def get_game_results(game_id):
    try:
        game_service = GameService()
        result = game_service.get_game_results(game_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/game/list', methods=['GET'])
def list_user_games():
    try:
        user_id = request.args.get('user_id', 'default_user')
        limit = int(request.args.get('limit', 10))
        
        game_service = GameService()
        result = game_service.list_user_games(user_id, limit)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/list', methods=['GET'])
def list_gallery():
    try:
        sort = request.args.get('sort', 'new')
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search_query = request.args.get('q')

        gallery_service = GalleryService()
        result = gallery_service.list_gallery(
            sort=sort,
            category=category,
            page=page,
            page_size=page_size,
            search_query=search_query
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/<gallery_id>', methods=['GET'])
def get_gallery_card(gallery_id):
    try:
        gallery_service = GalleryService()
        result = gallery_service.get_gallery_card(gallery_id, increment_view=True)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/share', methods=['POST'])
def share_to_gallery():
    try:
        data = request.get_json()
        
        gallery_service = GalleryService()
        result = gallery_service.share_card(
            user_id=data.get('user_id', 'default_user'),
            card_id=data.get('card_id', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', 'default'),
            tags=data.get('tags')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/<gallery_id>/like', methods=['POST'])
def like_gallery_card(gallery_id):
    try:
        gallery_service = GalleryService()
        result = gallery_service.like_card(gallery_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/<gallery_id>', methods=['DELETE'])
def unshare_gallery_card(gallery_id):
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        gallery_service = GalleryService()
        result = gallery_service.unshare_card(user_id, gallery_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/categories', methods=['GET'])
def get_gallery_categories():
    try:
        gallery_service = GalleryService()
        result = gallery_service.get_categories()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/gallery/tags', methods=['GET'])
def get_popular_tags():
    try:
        limit = int(request.args.get('limit', 20))
        
        gallery_service = GalleryService()
        result = gallery_service.get_popular_tags(limit)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/data/images/<filename>', methods=['GET'])
def serve_image(filename):
    return send_from_directory(settings.IMAGES_DIR, filename)


@api_bp.route('/data/audio/<filename>', methods=['GET'])
def serve_audio(filename):
    return send_from_directory(settings.AUDIO_DIR, filename)


@api_bp.route('/storyline/create', methods=['POST'])
def create_storyline():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        title = data.get('title', '未命名故事线')
        description = data.get('description')
        text = data.get('text')
        split_mode = data.get('split_mode', 'paragraph')
        tags = data.get('tags')

        storyline_service = StorylineService()
        result = storyline_service.create_storyline(
            user_id=user_id,
            title=title,
            description=description,
            text=text,
            split_mode=split_mode,
            tags=tags
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/list', methods=['GET'])
def list_storylines():
    try:
        user_id = request.args.get('user_id', 'default_user')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        storyline_service = StorylineService()
        result = storyline_service.list_storylines(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>', methods=['GET'])
def get_storyline(storyline_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        storyline_service = StorylineService()
        result = storyline_service.get_storyline(user_id, storyline_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "故事线不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/reorder', methods=['POST'])
def reorder_storyline_cards(storyline_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        new_order = data.get('new_order', [])

        if not new_order:
            return jsonify({
                "success": False,
                "error": "新顺序不能为空"
            }), 400

        storyline_service = StorylineService()
        result = storyline_service.update_card_order(
            user_id=user_id,
            storyline_id=storyline_id,
            new_order=new_order
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/merge', methods=['POST'])
def merge_storyline_cards(storyline_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        card_ids = data.get('card_ids', [])
        new_text = data.get('new_text', '')

        if len(card_ids) < 2:
            return jsonify({
                "success": False,
                "error": "至少需要选择2张卡片进行合并"
            }), 400

        if not new_text.strip():
            return jsonify({
                "success": False,
                "error": "合并后的文本不能为空"
            }), 400

        storyline_service = StorylineService()
        result = storyline_service.merge_cards(
            user_id=user_id,
            storyline_id=storyline_id,
            card_ids=card_ids,
            new_text=new_text
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/split', methods=['POST'])
def split_storyline_card(storyline_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        card_id = data.get('card_id')
        split_index = data.get('split_index', 0)
        part1_text = data.get('part1_text', '')
        part2_text = data.get('part2_text', '')

        if not card_id:
            return jsonify({
                "success": False,
                "error": "请指定要拆分的卡片"
            }), 400

        if not part1_text.strip() or not part2_text.strip():
            return jsonify({
                "success": False,
                "error": "拆分后的两部分文本都不能为空"
            }), 400

        storyline_service = StorylineService()
        result = storyline_service.split_card(
            user_id=user_id,
            storyline_id=storyline_id,
            card_id=card_id,
            split_index=split_index,
            part1_text=part1_text,
            part2_text=part2_text
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/card/<card_id>/tags', methods=['POST'])
def update_storyline_card_tags(storyline_id, card_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        tags = data.get('tags', [])
        action = data.get('action', 'set')

        storyline_service = StorylineService()
        result = storyline_service.update_card_tags(
            user_id=user_id,
            storyline_id=storyline_id,
            card_id=card_id,
            tags=tags,
            action=action
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/card/<card_id>/text', methods=['POST'])
def update_storyline_card_text(storyline_id, card_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        new_text = data.get('new_text', '')

        if not new_text.strip():
            return jsonify({
                "success": False,
                "error": "卡片文本不能为空"
            }), 400

        storyline_service = StorylineService()
        result = storyline_service.update_card_text(
            user_id=user_id,
            storyline_id=storyline_id,
            card_id=card_id,
            new_text=new_text
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/card', methods=['POST'])
def add_storyline_card(storyline_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        text = data.get('text', '')
        insert_after = data.get('insert_after')

        if not text.strip():
            return jsonify({
                "success": False,
                "error": "卡片文本不能为空"
            }), 400

        storyline_service = StorylineService()
        result = storyline_service.add_card(
            user_id=user_id,
            storyline_id=storyline_id,
            text=text,
            insert_after=insert_after
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>/card/<card_id>', methods=['DELETE'])
def delete_storyline_card(storyline_id, card_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        storyline_service = StorylineService()
        result = storyline_service.delete_card(
            user_id=user_id,
            storyline_id=storyline_id,
            card_id=card_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>', methods=['DELETE'])
def delete_storyline(storyline_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        storyline_service = StorylineService()
        result = storyline_service.delete_storyline(
            user_id=user_id,
            storyline_id=storyline_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/storyline/<storyline_id>', methods=['PUT'])
def update_storyline(storyline_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        title = data.get('title')
        description = data.get('description')
        tags = data.get('tags')

        storyline_service = StorylineService()
        result = storyline_service.update_storyline(
            user_id=user_id,
            storyline_id=storyline_id,
            title=title,
            description=description,
            tags=tags
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/create', methods=['POST'])
def create_collab_session():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        title = data.get('title', '未命名协作')
        description = data.get('description')
        initial_text = data.get('initial_text')
        style_id = data.get('style_id')
        world_setting_id = data.get('world_setting_id')

        collab_service = CollabWritingService()
        result = collab_service.create_session(
            user_id=user_id,
            title=title,
            description=description,
            initial_text=initial_text,
            style_id=style_id,
            world_setting_id=world_setting_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/list', methods=['GET'])
def list_collab_sessions():
    try:
        user_id = request.args.get('user_id', 'default_user')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        collab_service = CollabWritingService()
        result = collab_service.list_sessions(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>', methods=['GET'])
def get_collab_session(session_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        collab_service = CollabWritingService()
        result = collab_service.get_session(user_id, session_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "协作会话不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/write', methods=['POST'])
def user_collab_write(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        content = data.get('content', '')

        if not content.strip():
            return jsonify({
                "success": False,
                "error": "内容不能为空"
            }), 400

        collab_service = CollabWritingService()
        result = collab_service.user_write(
            user_id=user_id,
            session_id=session_id,
            content=content
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/ai-continue', methods=['POST'])
def ai_collab_continue(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        branch_count = data.get('branch_count', 3)

        volcengine = _get_volcengine_service(request.headers, data)
        collab_service = CollabWritingService()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                collab_service.ai_continue(
                    user_id=user_id,
                    session_id=session_id,
                    volcengine_service=volcengine,
                    branch_count=branch_count
                )
            )
        finally:
            loop.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/select-branch', methods=['POST'])
def select_collab_branch(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        branch_id = data.get('branch_id')

        if not branch_id:
            return jsonify({
                "success": False,
                "error": "请指定要选择的分支"
            }), 400

        collab_service = CollabWritingService()
        result = collab_service.select_branch(
            user_id=user_id,
            session_id=session_id,
            branch_id=branch_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/style', methods=['POST'])
def set_collab_style(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        style_id = data.get('style_id')

        if not style_id:
            return jsonify({
                "success": False,
                "error": "请指定写作风格"
            }), 400

        collab_service = CollabWritingService()
        result = collab_service.set_writing_style(
            user_id=user_id,
            session_id=session_id,
            style_id=style_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/character', methods=['POST'])
def add_collab_character(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        name = data.get('name', '')
        description = data.get('description', '')
        personality = data.get('personality')
        background = data.get('background')
        traits = data.get('traits')

        if not name.strip():
            return jsonify({
                "success": False,
                "error": "角色名称不能为空"
            }), 400

        collab_service = CollabWritingService()
        result = collab_service.add_character(
            user_id=user_id,
            session_id=session_id,
            name=name,
            description=description,
            personality=personality,
            background=background,
            traits=traits
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>/world-setting', methods=['POST'])
def add_collab_world_setting(session_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        name = data.get('name', '')
        description = data.get('description', '')
        genre = data.get('genre')
        era = data.get('era')
        rules = data.get('rules')

        if not name.strip():
            return jsonify({
                "success": False,
                "error": "世界观名称不能为空"
            }), 400

        collab_service = CollabWritingService()
        result = collab_service.add_world_setting(
            user_id=user_id,
            session_id=session_id,
            name=name,
            description=description,
            genre=genre,
            era=era,
            rules=rules
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/styles', methods=['GET'])
def get_collab_preset_styles():
    try:
        collab_service = CollabWritingService()
        result = collab_service.get_preset_styles()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/world-settings', methods=['GET'])
def get_collab_preset_world_settings():
    try:
        collab_service = CollabWritingService()
        result = collab_service.get_preset_world_settings()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/collab/<session_id>', methods=['DELETE'])
def delete_collab_session(session_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        collab_service = CollabWritingService()
        result = collab_service.delete_session(
            user_id=user_id,
            session_id=session_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/analyze', methods=['POST'])
def create_vivid_analysis():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        source_type = data.get('source_type', 'custom')
        source_id = data.get('source_id', str(uuid.uuid4()))
        title = data.get('title', '未命名分析')
        segments = data.get('segments', [])
        use_ai = data.get('use_ai', False)

        if not segments:
            return jsonify({
                "success": False,
                "error": "分析内容不能为空"
            }), 400

        vivid_service = VividMirrorService()

        if use_ai:
            volcengine = _get_volcengine_service(request.headers, data)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    vivid_service.analyze_with_ai(
                        user_id=user_id,
                        source_type=source_type,
                        source_id=source_id,
                        title=title,
                        segments=segments,
                        volcengine_service=volcengine
                    )
                )
            finally:
                loop.close()
        else:
            result = vivid_service.create_analysis(
                user_id=user_id,
                source_type=source_type,
                source_id=source_id,
                title=title,
                segments=segments
            )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/list', methods=['GET'])
def list_vivid_analyses():
    try:
        user_id = request.args.get('user_id', 'default_user')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        vivid_service = VividMirrorService()
        result = vivid_service.list_analyses(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>', methods=['GET'])
def get_vivid_analysis(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.get_analysis(user_id, analysis_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "分析不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>/emotion-heatmap', methods=['GET'])
def get_vivid_emotion_heatmap(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.get_emotion_heatmap(user_id, analysis_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "分析不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>/plot-heatmap', methods=['GET'])
def get_vivid_plot_heatmap(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.get_plot_heatmap(user_id, analysis_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "分析不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>/character-graph', methods=['GET'])
def get_vivid_character_graph(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.get_character_graph(user_id, analysis_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "分析不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>/argument-graph', methods=['GET'])
def get_vivid_argument_graph(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.get_argument_graph(user_id, analysis_id)

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "分析不存在"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>/find-segment', methods=['GET'])
def find_vivid_segment_by_node(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')
        node_type = request.args.get('node_type')
        node_id = request.args.get('node_id')

        if not node_type or not node_id:
            return jsonify({
                "success": False,
                "error": "请指定节点类型和节点ID"
            }), 400

        vivid_service = VividMirrorService()
        result = vivid_service.find_segment_by_node(
            user_id=user_id,
            analysis_id=analysis_id,
            node_type=node_type,
            node_id=node_id
        )

        if result:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "未找到对应的段落"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/vivid/<analysis_id>', methods=['DELETE'])
def delete_vivid_analysis(analysis_id):
    try:
        user_id = request.args.get('user_id', 'default_user')

        vivid_service = VividMirrorService()
        result = vivid_service.delete_analysis(
            user_id=user_id,
            analysis_id=analysis_id
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

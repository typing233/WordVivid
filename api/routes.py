from flask import Blueprint, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import uuid

from config import get_settings, IMAGE_STYLES, VOICE_TYPES
from services.volcengine_service import VolcEngineService
from services.card_generator import CardGeneratorService
from services.memory_library import MemoryLibraryService
from services.game_service import GameService
from services.gallery_service import GalleryService
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
async def process_text():
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
        segments = await volcengine.split_text_smart(text, split_mode)

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
async def generate_card():
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
        
        result = await card_service.generate_card(
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
async def generate_cards_batch():
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
        
        result = await card_service.generate_cards_batch(
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
async def submit_answer():
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
        
        result = await game_service.submit_answer(
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

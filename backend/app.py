"""
Flask后端应用
提供围棋游戏API
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import uuid

from app.game_manager import game_manager

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
CORS(app)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/game/new', methods=['POST'])
def new_game():
    """创建新游戏"""
    data = request.get_json()
    difficulty = data.get('difficulty', 'medium')
    size = data.get('size', 19)
    ai_color = data.get('ai_color', 2)  # 2 = 白棋

    game_id = str(uuid.uuid4())
    game_info = game_manager.create_game(game_id, difficulty, size, ai_color)

    return jsonify({
        'success': True,
        'game': game_info
    })


@app.route('/api/game/<game_id>/move', methods=['POST'])
def make_move(game_id):
    """落子"""
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')

    if x is None or y is None:
        return jsonify({'error': '缺少坐标参数'}), 400

    result = game_manager.make_move(game_id, x, y)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/game/<game_id>/ai-move', methods=['POST'])
def ai_move(game_id):
    """AI落子（异步接口）"""
    result = game_manager.make_ai_move(game_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/game/<game_id>/pass', methods=['POST'])
def pass_turn(game_id):
    """虚着"""
    result = game_manager.pass_turn(game_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/game/<game_id>/valid-moves', methods=['GET'])
def get_valid_moves(game_id):
    """获取合法落子位置"""
    result = game_manager.get_valid_moves(game_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/game/<game_id>/score', methods=['GET'])
def get_score(game_id):
    """获取分数"""
    result = game_manager.get_score(game_id)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/ai/explain', methods=['POST'])
def explain_move():
    """让AI解释某个位置的思考（不实际落子）"""
    data = request.get_json()
    game_id = data.get('game_id')
    x = data.get('x')
    y = data.get('y')

    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404

    # 创建临时AI来获取解释
    from app.go_ai import create_ai
    temp_board = game['board'].__class__(game['board'].size)
    temp_board.board = [row[:] for row in game['board'].board]
    temp_board.current_player = game['board'].current_player

    temp_ai = create_ai(temp_board, game['ai_color'], game['difficulty'])

    # 模拟落子并获取解释
    temp_board.place_stone(x, y)
    _, _, explanation = temp_ai.get_move()

    return jsonify({
        'explanation': explanation
    })


@app.route('/api/game/<game_id>/analyze', methods=['POST'])
def analyze_position(game_id):
    """分析当前局势"""
    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404

    from app.go_ai import AdvancedAI
    board = game['board']

    # 创建AI分析器
    ai = AdvancedAI(board, board.current_player, game['difficulty'])

    # 分析双方局势
    analysis = {
        'game_phase': ai.game_phase,
        'move_count': len(board.move_history),
        'current_player': '黑方' if board.current_player == 1 else '白方',
        'black_strength': _analyze_player_strength(board, 1),
        'white_strength': _analyze_player_strength(board, 2),
        'territory': _analyze_territory(board),
        'influence': _analyze_influence(board),
        'recommendations': _get_recommendations(board, ai),
        'overall_assessment': _get_overall_assessment(board)
    }

    return jsonify(analysis)


@app.route('/api/game/<game_id>/logs', methods=['GET'])
def get_game_logs(game_id):
    """获取落子日志"""
    game = game_manager.get_game(game_id)
    if not game:
        return jsonify({'error': '游戏不存在'}), 404

    board = game['board']

    # 格式化日志
    logs = []
    for i, move in enumerate(board.move_history):
        if move['x'] == -1:  # 虚着
            log_entry = {
                'number': i + 1,
                'player': '黑方' if move['player'] == 1 else '白方',
                'player_color': move['player'],
                'action': '虚着',
                'captured': 0
            }
        else:
            # 计算围棋坐标（如K4、Q10等）
            x_letter = chr(65 + move['x'])  # A, B, C, ...
            y_coord = board.size - move['y']

            log_entry = {
                'number': i + 1,
                'player': '黑方' if move['player'] == 1 else '白方',
                'player_color': move['player'],
                'action': f"{x_letter}{y_coord}",
                'position': f"({move['x'] + 1}, {move['y'] + 1})",
                'captured': move.get('captured', 0)
            }

        logs.append(log_entry)

    return jsonify({
        'logs': logs,
        'total_moves': len(board.move_history)
    })


def _analyze_player_strength(board, player):
    """分析某方棋力"""
    stones = 0
    groups = []
    visited = set()

    for y in range(board.size):
        for x in range(board.size):
            if board.board[y][x] == player and (x, y) not in visited:
                from app.go_ai import AdvancedAI
                # 创建临时AI实例来使用其方法
                temp_ai = AdvancedAI(board, player, 'medium')
                group = temp_ai._get_group(x, y, player)
                groups.append(len(group))
                visited.update(group)
                stones += len(group)

    avg_group_size = sum(groups) / len(groups) if groups else 0

    return {
        'stones': stones,
        'groups': len(groups),
        'avg_group_size': round(avg_group_size, 1),
        'captured': board.captured_black if player == 1 else board.captured_white
    }


def _analyze_territory(board):
    """分析领地"""
    black_territory = 0
    white_territory = 0
    neutral = 0

    for y in range(board.size):
        for x in range(board.size):
            if board.board[y][x] == 0:
                owner = board._get_territory_owner(x, y)
                if owner == 1:
                    black_territory += 1
                elif owner == 2:
                    white_territory += 1
                else:
                    neutral += 1
            elif board.board[y][x] == 1:
                black_territory += 1
            else:
                white_territory += 1

    return {
        'black': black_territory,
        'white': white_territory,
        'neutral': neutral,
        'black_advantage': black_territory - white_territory
    }


def _analyze_influence(board):
    """分析影响力"""
    black_influence = 0
    white_influence = 0

    for y in range(board.size):
        for x in range(board.size):
            # 计算每个位置的影响力
            influence_range = 3
            for dy in range(-influence_range, influence_range + 1):
                for dx in range(-influence_range, influence_range + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < board.size and 0 <= ny < board.size:
                        dist = max(abs(dx), abs(dy))
                        if dist > 0:
                            weight = 1 / dist
                            if board.board[ny][nx] == 1:
                                black_influence += weight
                            elif board.board[ny][nx] == 2:
                                white_influence += weight

    return {
        'black': round(black_influence, 1),
        'white': round(white_influence, 1),
        'domination': '黑方' if black_influence > white_influence else '白方'
    }


def _get_recommendations(board, ai):
    """获取建议"""
    recommendations = []

    move_count = len(board.move_history)

    if ai.game_phase == "opening":
        recommendations.append("开局阶段：重视角边，占据星位是好选择")
        if move_count < 10:
            recommendations.append("建议：先在角部落子建立根基")
    elif ai.game_phase == "middlegame":
        recommendations.append("中盘阶段：注意战斗和实地平衡")
        recommendations.append("建议：关注切断对方和连接己方的机会")
    else:
        recommendations.append("官子阶段：抢占边界，计算目数")
        recommendations.append("建议：仔细计算每个官子的价值")

    return recommendations


def _get_overall_assessment(board):
    """总体评估"""
    black_score, white_score = board.get_score()
    diff = black_score - white_score

    if diff > 10:
        winner = "黑方大幅领先"
        emoji = "⚫"
    elif diff > 5:
        winner = "黑方略占优势"
        emoji = "⚫"
    elif diff > -5:
        winner = "局势胶着，胜负未分"
        emoji = "⚖️"
    elif diff > -10:
        winner = "白方略占优势"
        emoji = "⚪"
    else:
        winner = "白方大幅领先"
        emoji = "⚪"

    return {
        'winner': winner,
        'emoji': emoji,
        'score_diff': round(diff, 1),
        'black_score': round(black_score, 1),
        'white_score': round(white_score, 1)
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

"""游戏状态管理"""

from .go_board import GoBoard
from .go_ai import create_ai
from .deepseek_ai import create_deepseek_ai


class GameManager:
    """游戏管理器"""

    def __init__(self):
        self.games = {}

    def create_game(self, game_id: str, difficulty: str = "medium",
                    size: int = 19, ai_color: int = 2) -> dict:
        """创建新游戏"""
        board = GoBoard(size)
        # 使用本地AI快速决策，DeepSeek用于解释
        ai = create_ai(board, ai_color, difficulty)
        self.games[game_id] = {
            'board': board,
            'difficulty': difficulty,
            'ai_color': ai_color,
            'ai': ai,
            'game_over': False,
            'use_deepseek': True  # 标记是否使用DeepSeek增强解释
        }
        return {
            'game_id': game_id,
            'board_size': size,
            'current_player': board.current_player,
            'ai_color': ai_color
        }

    def get_game(self, game_id: str):
        """获取游戏"""
        return self.games.get(game_id)

    def make_move(self, game_id: str, x: int, y: int) -> dict:
        """玩家落子（立即返回，不等待AI）"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        if game['game_over']:
            return {'error': '游戏已结束'}

        board = game['board']

        # 检查是否轮到玩家
        if board.current_player == game['ai_color']:
            # AI的回合，直接让AI落子并返回
            ai_x, ai_y, explanation = game['ai'].get_move()

            result = {
                'success': True,
                'message': 'AI回合',
                'board': board.get_board_state(),
                'current_player': board.current_player,
                'captured_black': board.captured_black,
                'captured_white': board.captured_white,
                'last_move': board.last_move,
                'game_over': board.is_game_over(),
                'is_ai_turn': True
            }

            if ai_x >= 0:
                success, ai_message = board.place_stone(ai_x, ai_y)
                result['ai_move'] = {'x': ai_x, 'y': ai_y}
                result['ai_explanation'] = explanation
                result['message'] = ai_message
            else:
                board.pass_move()
                result['ai_move'] = None
                result['ai_explanation'] = "我选择虚着"

            result['board'] = board.get_board_state()
            result['current_player'] = board.current_player
            result['captured_black'] = board.captured_black
            result['captured_white'] = board.captured_white
            result['last_move'] = board.last_move

            if board.is_game_over():
                game['game_over'] = True
                black_score, white_score = board.get_score()
                result['game_over'] = True
                result['score'] = {'black': black_score, 'white': white_score}
                result['winner'] = 'black' if black_score > white_score else 'white'

            return result

        # 玩家落子 - 立即返回，不等待AI
        success, message = board.place_stone(x, y)

        if not success:
            return {'error': message}

        result = {
            'success': True,
            'message': message,
            'board': board.get_board_state(),
            'current_player': board.current_player,
            'captured_black': board.captured_black,
            'captured_white': board.captured_white,
            'last_move': board.last_move,
            'game_over': board.is_game_over(),
            'is_ai_turn': True  # 告诉前端接下来是AI回合
        }

        # 检查游戏是否结束
        if board.is_game_over():
            game['game_over'] = True
            black_score, white_score = board.get_score()
            result['score'] = {'black': black_score, 'white': white_score}
            result['winner'] = 'black' if black_score > white_score else 'white'
            result['is_ai_turn'] = False

        return result

    def make_ai_move(self, game_id: str) -> dict:
        """AI落子（单独的接口）"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        if game['game_over']:
            return {'error': '游戏已结束'}

        board = game['board']

        if board.current_player != game['ai_color']:
            return {'error': '不是AI回合'}

        # AI落子（使用本地AI快速决策）
        ai_x, ai_y, basic_explanation = game['ai'].get_move()

        result = {
            'success': True,
            'board': board.get_board_state(),
            'current_player': board.current_player,
            'captured_black': board.captured_black,
            'captured_white': board.captured_white,
            'last_move': board.last_move,
            'game_over': board.is_game_over()
        }

        if ai_x >= 0:
            success, message = board.place_stone(ai_x, ai_y)
            result['ai_move'] = {'x': ai_x, 'y': ai_y}
            result['ai_explanation'] = basic_explanation
            result['message'] = message

            # 如果启用DeepSeek增强且不是简单模式，异步获取详细解释
            # 注意：这里先返回基础解释，详细解释可以后续优化
        else:
            board.pass_move()
            result['ai_move'] = None
            result['ai_explanation'] = "我选择虚着"
            result['message'] = "AI虚着"

        result['board'] = board.get_board_state()
        result['current_player'] = board.current_player
        result['captured_black'] = board.captured_black
        result['captured_white'] = board.captured_white
        result['last_move'] = board.last_move

        if board.is_game_over():
            game['game_over'] = True
            black_score, white_score = board.get_score()
            result['game_over'] = True
            result['score'] = {'black': black_score, 'white': white_score}
            result['winner'] = 'black' if black_score > white_score else 'white'

        return result

    def pass_turn(self, game_id: str) -> dict:
        """玩家虚着"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        if game['game_over']:
            return {'error': '游戏已结束'}

        board = game['board']
        board.pass_move()

        result = {
            'success': True,
            'message': '虚着',
            'board': board.get_board_state(),
            'current_player': board.current_player
        }

        # AI落子
        if board.current_player == game['ai_color']:
            ai_x, ai_y, explanation = game['ai'].get_move()

            if ai_x >= 0:
                board.place_stone(ai_x, ai_y)
                result['ai_move'] = {'x': ai_x, 'y': ai_y}
                result['ai_explanation'] = explanation
            else:
                board.pass_move()
                result['ai_move'] = None
                result['ai_explanation'] = "我选择虚着"

            result['board'] = board.get_board_state()
            result['current_player'] = board.current_player
            result['captured_black'] = board.captured_black
            result['captured_white'] = board.captured_white

            if board.is_game_over():
                game['game_over'] = True
                black_score, white_score = board.get_score()
                result['game_over'] = True
                result['score'] = {'black': black_score, 'white': white_score}
                result['winner'] = 'black' if black_score > white_score else 'white'

        return result

    def get_valid_moves(self, game_id: str) -> dict:
        """获取合法落子位置"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        return {
            'valid_moves': game['board'].get_valid_moves()
        }

    def undo_move(self, game_id: str) -> dict:
        """悔棋（回退两步：玩家和AI各一步）"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        board = game['board']

        if len(board.move_history) < 2:
            return {'error': '没有可以悔棋的步骤'}

        # 回退AI的落子
        board.move_history.pop()
        # 回退玩家的落子
        last_player_move = board.move_history.pop()

        # 重建棋盘状态
        # 注意：完整的悔棋实现需要重新执行所有历史步骤
        # 这里简化处理，只提示功能
        return {'error': '悔棋功能需要重新实现'}

    def get_score(self, game_id: str) -> dict:
        """获取当前分数"""
        game = self.get_game(game_id)
        if not game:
            return {'error': '游戏不存在'}

        black_score, white_score = game['board'].get_score()
        return {
            'black_score': black_score,
            'white_score': white_score
        }


# 全局游戏管理器
game_manager = GameManager()

"""
围棋AI引擎 - 升级版
更强的围棋AI，使用更深入的评估和策略
"""

import random
from typing import Tuple, List, Dict, Set
from .go_board import GoBoard


class GoAI:
    """围棋AI基类"""

    def __init__(self, board: GoBoard, player: int, difficulty: str = "medium"):
        self.board = board
        self.player = player  # AI执黑或执白
        self.difficulty = difficulty
        self.opponent = 3 - player

    def get_move(self) -> Tuple[int, int, str]:
        """
        获取AI的落子位置和解释
        返回: (x, y, explanation)
        """
        raise NotImplementedError


class AdvancedAI(GoAI):
    """高级AI - 使用深度评估和战术分析"""

    def __init__(self, board: GoBoard, player: int, difficulty: str = "medium"):
        super().__init__(board, player, difficulty)
        self.move_count = len(board.move_history)
        self.game_phase = self._determine_game_phase()

    def _determine_game_phase(self) -> str:
        """判断游戏阶段"""
        if self.move_count < 40:
            return "opening"
        elif self.move_count < 120:
            return "middlegame"
        else:
            return "endgame"

    def get_move(self) -> Tuple[int, int, str]:
        """获取最佳落子"""
        valid_moves = self.board.get_valid_moves()

        if not valid_moves:
            return -1, -1, "没有合法的落子位置，选择虚着"

        # 根据难度调整搜索深度
        if self.difficulty == "easy":
            return self._get_move_simple(valid_moves)
        elif self.difficulty == "hard":
            return self._get_move_advanced(valid_moves)
        else:
            return self._get_move_medium(valid_moves)

    def _get_move_advanced(self, valid_moves: List[Tuple[int, int]]) -> Tuple[int, int, str]:
        """困难模式 - 深度分析"""
        best_score = -float('inf')
        best_move = None
        analyses = []

        # 对每个候选点进行深入评估
        for x, y in valid_moves:
            score, analysis = self._evaluate_move_deep(x, y)

            # 添加随机性保持变化
            score += random.random() * 0.5

            if score > best_score:
                best_score = score
                best_move = (x, y)
                analyses = [analysis]
            elif score > best_score - 2:
                analyses.append(analysis)

        explanation = self._format_explanation(best_move[0], best_move[1], analyses[:3])
        return best_move[0], best_move[1], explanation

    def _evaluate_move_deep(self, x: int, y: int) -> Tuple[float, str]:
        """深度评估某个落子"""
        score = 0
        reasons = []

        # 1. 战术价值 (权重最高)
        tactical_score, tactical_reason = self._evaluate_tactical(x, y)
        score += tactical_score * 2.5
        if tactical_score > 10:
            reasons.append(tactical_reason)

        # 2. 位置价值
        position_score, position_reason = self._evaluate_position_advanced(x, y)
        score += position_score * 1.5
        if position_score > 15:
            reasons.append(position_reason)

        # 3. 形状价值
        shape_score, shape_reason = self._evaluate_shape(x, y)
        score += shape_score * 1.2
        if shape_score > 10:
            reasons.append(shape_reason)

        # 4. 厚势与影响力
        influence_score, influence_reason = self._evaluate_influence(x, y)
        score += influence_score
        if influence_score > 8:
            reasons.append(influence_reason)

        # 5. 领地价值
        territory_score, territory_reason = self._evaluate_territory(x, y)
        score += territory_score
        if territory_score > 8:
            reasons.append(territory_reason)

        analysis = f"({x+1},{y+1}) " + "、".join(reasons[:3]) if reasons else f"({x+1},{y+1}) 综合评估"
        return score, analysis

    def _evaluate_tactical(self, x: int, y: int) -> Tuple[float, str]:
        """战术评估"""
        score = 0
        reasons = []

        # 检查是否能提吃对方
        can_capture, capture_count = self._can_capture_stones(x, y)
        if can_capture:
            score += 30 + capture_count * 5
            reasons.append(f"可提吃{capture_count}子")

        # 检查是否能救己方
        can_save, save_count = self._can_save_stones(x, y)
        if can_save:
            score += 25 + save_count * 3
            reasons.append(f"救回{save_count}子")

        # 检查是否会被提
        if self._will_be_captured(x, y):
            score -= 50
            reasons.append("会被提吃")

        # 检查切断
        if self._can_cut(x, y):
            score += 20
            reasons.append("切断对方")

        # 检查连接
        if self._can_connect(x, y):
            score += 15
            reasons.append("连接己方")

        # 检查征子
        if self._is_ladder(x, y):
            score -= 30
            reasons.append("会被征吃")

        return score, "、".join(reasons)

    def _evaluate_position_advanced(self, x: int, y: int) -> Tuple[float, str]:
        """高级位置评估"""
        score = 0
        size = self.board.size

        if self.game_phase == "opening":
            # 开局重视角边
            if self._is_corner_star(x, y):
                score += 25
                return score, "占据星位"
            elif self._is_side_star(x, y):
                score += 20
                return score, "边星位"
            elif self._is_good_opening_point(x, y):
                score += 18
                return score, "好点"

            # 第三线、第四线加分
            line = min(x, y, size - 1 - x, size - 1 - y)
            if 2 <= line <= 4:
                score += 12
                return score, "第三、四线"
            elif line > 4:
                score -= 5  # 开局太浅

        elif self.game_phase == "middlegame":
            # 中盘重视中央和战斗
            center_dist = abs(x - size // 2) + abs(y - size // 2)
            score += max(0, 15 - center_dist * 0.5)

            # 靠近对方棋子
            if self._near_enemy_stones(x, y):
                score += 15
                return score, "接近战斗"

        elif self.game_phase == "endgame":
            # 官子阶段重视边界和实地
            territory_value = self._count_endgame_value(x, y)
            score += territory_value
            if territory_value > 10:
                return score, f"官子价值{territory_value}目"

        return score, ""

    def _evaluate_shape(self, x: int, y: int) -> Tuple[float, str]:
        """形状评估"""
        score = 0

        # 检查是否是好形
        if self._makes_good_shape(x, y):
            score += 15
            return score, "好形"

        # 检查是否是愚形
        if self._makes_bad_shape(x, y):
            score -= 15
            return score, "愚形(避免)"

        # 检查效率
        efficiency = self._calculate_efficiency(x, y)
        score += efficiency
        if efficiency > 12:
            return score, f"高效率{effiveness:.0f}分"

        return score, ""

    def _evaluate_influence(self, x: int, y: int) -> Tuple[float, str]:
        """影响力评估"""
        score = 0

        # 计算厚势
        thickness = self._calculate_thickness(x, y)
        score += thickness

        # 计算先手价值
        if self._keeps_initiative(x, y):
            score += 12
            return score + thickness, "保持先手"

        return score, ""

    def _evaluate_territory(self, x: int, y: int) -> Tuple[float, str]:
        """领地评估"""
        # 评估这个位置能控制多少领地
        territory = self._estimate_territory_control(x, y)
        return territory, f"控制{territory:.0f}目"

    def _can_capture_stones(self, x: int, y: int) -> Tuple[bool, int]:
        """检查是否能提吃对方棋子"""
        import copy
        temp_board = copy.deepcopy(self.board.board)
        temp_board[y][x] = self.player

        captured = []
        opponent = self.opponent
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if temp_board[ny][nx] == opponent:
                    if not self._has_liberty_board(temp_board, nx, ny, opponent):
                        group = self._get_group_board(temp_board, nx, ny, opponent)
                        captured.extend(group)

        return len(captured) > 0, len(captured)

    def _can_save_stones(self, x: int, y: int) -> Tuple[bool, int]:
        """检查是否能救己方棋子"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        saved_count = 0

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    # 检查这个棋子组是否只有1口气
                    liberties = self._count_group_liberties_board(nx, ny, self.player)
                    if liberties == 1:
                        saved_count += len(self._get_group(nx, ny, self.player))

        return saved_count > 0, saved_count

    def _will_be_captured(self, x: int, y: int) -> bool:
        """检查落子后是否会被立即提吃"""
        import copy
        temp_board = copy.deepcopy(self.board.board)
        temp_board[y][x] = self.player

        # 检查自己这组棋的气
        if not self._has_liberty_board(temp_board, x, y, self.player):
            # 除非能提吃对方
            captured = 0
            opponent = self.opponent
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if temp_board[ny][nx] == opponent:
                        if not self._has_liberty_board(temp_board, nx, ny, opponent):
                            captured += 1

            return captured == 0

        return False

    def _has_liberty_board(self, board: List[List[int]], x: int, y: int, player: int) -> bool:
        """检查指定棋盘上某位置是否有气"""
        group = self._get_group_board(board, x, y, player)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if board[ny][nx] == 0:
                        return True
        return False

    def _get_group_board(self, board: List[List[int]], x: int, y: int, player: int) -> Set[Tuple[int, int]]:
        """获取指定棋盘上的棋子组"""
        group = set()
        stack = [(x, y)]
        visited = set()
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            if 0 <= cx < self.board.size and 0 <= cy < self.board.size and board[cy][cx] == player:
                group.add((cx, cy))
                for dx, dy in directions:
                    stack.append((cx + dx, cy + dy))

        return group

    def _count_group_liberties_board(self, x: int, y: int, player: int) -> int:
        """计算棋子组的气数"""
        group = self._get_group(x, y, player)
        liberties = set()
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if self.board.board[ny][nx] == 0:
                        liberties.add((nx, ny))

        return len(liberties)

    def _can_cut(self, x: int, y: int) -> bool:
        """检查是否能切断对方"""
        enemy_neighbors = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.opponent:
                    enemy_neighbors.append((nx, ny))

        # 如果有多个对方棋子，且它们不在同一组
        if len(enemy_neighbors) >= 2:
            groups = set()
            for nx, ny in enemy_neighbors:
                group = frozenset(self._get_group(nx, ny, self.opponent))
                groups.add(group)
            return len(groups) >= 2

        return False

    def _can_connect(self, x: int, y: int) -> bool:
        """检查是否能连接己方"""
        friendly_neighbors = 0
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    friendly_neighbors += 1

        return friendly_neighbors >= 2

    def _is_ladder(self, x: int, y: int) -> bool:
        """简化版征子检查"""
        # 检查是否有对方的征子模式
        return False  # 简化实现

    def _is_corner_star(self, x: int, y: int) -> bool:
        """检查是否是角星位"""
        size = self.board.size
        if size == 19:
            corner_stars = [(3, 3), (3, 15), (15, 3), (15, 15)]
            return (x, y) in corner_stars
        elif size == 13:
            corner_stars = [(3, 3), (3, 9), (9, 3), (9, 9)]
            return (x, y) in corner_stars
        return False

    def _is_side_star(self, x: int, y: int) -> bool:
        """检查是否是边星位"""
        size = self.board.size
        if size == 19:
            side_stars = [(9, 3), (9, 15), (3, 9), (15, 9)]
            return (x, y) in side_stars
        elif size == 13:
            side_stars = [(6, 3), (6, 9), (3, 6), (9, 6)]
            return (x, y) in side_stars
        return False

    def _is_good_opening_point(self, x: int, y: int) -> bool:
        """检查是否是好开局点"""
        size = self.board.size
        if size == 19:
            # 小目、目外等
            good_points = [(2, 3), (3, 2), (2, 15), (15, 2), (16, 3), (3, 16), (16, 15), (15, 16)]
            return (x, y) in good_points
        return False

    def _near_enemy_stones(self, x: int, y: int, distance: int = 2) -> bool:
        """检查是否靠近对方棋子"""
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if self.board.board[ny][nx] == self.opponent:
                        return True
        return False

    def _makes_good_shape(self, x: int, y: int) -> bool:
        """检查是否形成好形"""
        # 检查是否能形成良好的连接
        friendly = 0
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    friendly += 1

        # 形成竹节等好形
        return friendly >= 2

    def _makes_bad_shape(self, x: int, y: int) -> bool:
        """检查是否形成愚形"""
        # 简化检查：避免空三角等
        friendly_count = 0
        diagonal_count = 0

        # 检查相邻
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    friendly_count += 1

        # 检查对角
        for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    diagonal_count += 1

        # 空三角：相邻2子+对角1子
        if friendly_count == 2 and diagonal_count >= 1:
            return True

        return False

    def _calculate_efficiency(self, x: int, y: int) -> float:
        """计算落子效率"""
        # 基于影响力范围
        efficiency = 0
        for r in range(1, 4):
            influence_count = 0
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                        if self.board.board[ny][nx] == self.player:
                            influence_count += 1
                        elif self.board.board[ny][nx] == self.opponent:
                            influence_count += 0.5
            efficiency += influence_count / r

        return efficiency

    def _calculate_thickness(self, x: int, y: int) -> float:
        """计算厚势"""
        thickness = 0
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if self.board.board[ny][nx] == self.player:
                        dist = max(abs(dx), abs(dy))
                        thickness += (4 - dist) / 2

        return thickness

    def _keeps_initiative(self, x: int, y: int) -> bool:
        """检查是否保持先手"""
        # 如果落子后能威胁对方，就是先手
        return self._near_enemy_stones(x, y, 1)

    def _estimate_territory_control(self, x: int, y: int) -> float:
        """估算领地控制"""
        territory = 0
        checked = set()
        stack = [(x, y)]

        while stack and len(checked) < 20:
            cx, cy = stack.pop()
            if (cx, cy) in checked:
                continue
            checked.add((cx, cy))

            if not (0 <= cx < self.board.size and 0 <= cy < self.board.size):
                continue

            if self.board.board[cy][cx] == 0:
                territory += 1
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    stack.append((cx + dx, cy + dy))

        return territory

    def _count_endgame_value(self, x: int, y: int) -> float:
        """计算官子价值"""
        # 简化实现
        value = 5

        # 靠近边界更有价值
        edge_dist = min(x, y, self.board.size - 1 - x, self.board.size - 1 - y)
        if edge_dist <= 2:
            value += 5

        # 靠近己方棋子
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                if self.board.board[ny][nx] == self.player:
                    value += 3

        return value

    def _get_group(self, x: int, y: int, player: int) -> Set[Tuple[int, int]]:
        """获取棋子组"""
        group = set()
        stack = [(x, y)]
        visited = set()
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            if 0 <= cx < self.board.size and 0 <= cy < self.board.size and self.board.board[cy][cx] == player:
                group.add((cx, cy))
                for dx, dy in directions:
                    stack.append((cx + dx, cy + dy))

        return group

    def _format_explanation(self, x: int, y: int, analyses: List[str]) -> str:
        """格式化解释"""
        if not analyses:
            return f"选择 ({x+1},{y+1})：经过综合分析，这是当前最佳选择"

        main_analysis = analyses[0] if analyses else ""
        return f"选择 ({x+1},{y+1})：\n  • {main_analysis}"

    def _get_move_medium(self, valid_moves: List[Tuple[int, int]]) -> Tuple[int, int, str]:
        """中等模式"""
        best_score = -float('inf')
        best_move = valid_moves[0]

        for x, y in valid_moves:
            score = 0

            # 简化评估
            if self._can_capture_stones(x, y)[0]:
                score += 25
            if self._can_save_stones(x, y)[0]:
                score += 20
            if self._will_be_captured(x, y):
                score -= 40
            if self._can_cut(x, y):
                score += 15
            if self._can_connect(x, y):
                score += 12

            # 位置评分
            position_score, _ = self._evaluate_position_advanced(x, y)
            score += position_score * 0.8

            score += random.random() * 3

            if score > best_score:
                best_score = score
                best_move = (x, y)

        x, y = best_move
        return x, y, f"选择 ({x+1},{y+1})：综合评估后的最佳选择"

    def _get_move_simple(self, valid_moves: List[Tuple[int, int]]) -> Tuple[int, int, str]:
        """简单模式"""
        # 30%概率随机
        if random.random() < 0.3:
            x, y = random.choice(valid_moves)
            return x, y, f"选择 ({x+1},{y+1})：尝试这个位置"

        best_score = -float('inf')
        best_move = valid_moves[0]

        for x, y in valid_moves:
            score = 0

            if self._can_capture_stones(x, y)[0]:
                score += 20
            if self._can_save_stones(x, y)[0]:
                score += 15
            if self._will_be_captured(x, y):
                score -= 30

            # 优先星位和边角
            if self.game_phase == "opening":
                if self._is_corner_star(x, y) or self._is_side_star(x, y):
                    score += 15

            score += random.random() * 5

            if score > best_score:
                best_score = score
                best_move = (x, y)

        x, y = best_move
        return x, y, f"选择 ({x+1},{y+1})：这步棋看起来不错"


def create_ai(board: GoBoard, player: int, difficulty: str = "medium") -> GoAI:
    """创建AI实例的工厂函数"""
    return AdvancedAI(board, player, difficulty)

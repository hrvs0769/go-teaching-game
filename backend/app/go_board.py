"""
围棋棋盘和游戏逻辑实现
完全符合中国围棋规则的实现
"""

from typing import List, Tuple, Optional, Set
import copy


class GoBoard:
    """围棋棋盘类 - 工业级实现"""

    def __init__(self, size: int = 19):
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]  # 0: 空, 1: 黑, 2: 白
        self.current_player = 1  # 1: 黑棋先手
        self.move_history = []
        self.captured_black = 0
        self.captured_white = 0
        self.ko_point = None  # 打劫点
        self.last_move = None

    def is_valid_move(self, x: int, y: int) -> bool:
        """检查落子是否合法"""
        # 基本边界检查
        if not (0 <= x < self.size and 0 <= y < self.size):
            return False

        # 位置必须为空
        if self.board[y][x] != 0:
            return False

        # 打劫规则
        if self.ko_point and (x, y) == self.ko_point:
            return False

        # 创建临时棋盘测试落子
        temp_board = [row[:] for row in self.board]
        temp_board[y][x] = self.current_player

        # 检查是否能提对方的子
        opponent = 3 - self.current_player
        can_capture = self._can_capture_anything(temp_board, x, y, opponent)

        # 如果不能提子，检查自己是否有气（禁止自杀）
        if not can_capture:
            if not self._has_any_liberty(temp_board, x, y, self.current_player):
                return False

        return True

    def _can_capture_anything(self, board: List[List[int]], x: int, y: int, opponent: int) -> bool:
        """
        检查落子后能否提吃对方的子

        关键：检查对方棋组是否有气时，必须排除当前落子位置(x,y)！
        """
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if board[ny][nx] == opponent:
                    # 获取对方棋子组
                    group = self._get_group_at(board, nx, ny, opponent)
                    # 检查这个组是否有气（排除当前落子位置）
                    # 因为我们将在(x,y)落子，对方不能利用这个位置作为气
                    if not self._group_has_liberty_excluding(board, group, opponent, x, y):
                        return True

        return False

    def _has_any_liberty(self, board: List[List[int]], x: int, y: int, player: int) -> bool:
        """检查某个位置的棋子组是否有气"""
        group = self._get_group_at(board, x, y, player)
        return self._group_has_liberty(board, group, player)

    def _group_has_liberty_excluding(self, board: List[List[int]], group: Set[Tuple[int, int]],
                                    player: int, exclude_x: int, exclude_y: int) -> bool:
        """检查棋子组是否有气（排除指定位置）"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                # 排除当前落子位置
                if (nx, ny) == (exclude_x, exclude_y):
                    continue
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if board[ny][nx] == 0:
                        return True
        return False

    def _group_has_liberty(self, board: List[List[int]], group: Set[Tuple[int, int]], player: int) -> bool:
        """检查棋子组是否有气"""
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if board[ny][nx] == 0:
                        return True
        return False

    def _get_group_at(self, board: List[List[int]], x: int, y: int, player: int, debug=False) -> Set[Tuple[int, int]]:
        """
        获取相连的棋子组
        使用优化的Flood Fill算法
        """
        if board[y][x] != player:
            if debug:
                print(f"[GROUP DEBUG] 起点({x},{y})不是{player}方棋子")
            return set()

        group = set()
        stack = [(x, y)]
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        iteration = 0
        while stack:
            iteration += 1
            cx, cy = stack.pop()

            if (cx, cy) in group:
                if debug and iteration <= 20:
                    print(f"[GROUP DEBUG] 跳过已处理位置: ({cx},{cy})")
                continue

            # 边界检查
            if not (0 <= cx < self.size and 0 <= cy < self.size):
                if debug and iteration <= 20:
                    print(f"[GROUP DEBUG] 超出边界: ({cx},{cy})")
                continue

            # 只处理相同颜色的棋子
            if board[cy][cx] != player:
                if debug and iteration <= 20:
                    print(f"[GROUP DEBUG] 位置({cx},{cy})不是{player}方棋子，而是{board[cy][cx]}方")
                continue

            group.add((cx, cy))
            if debug and iteration <= 20:
                print(f"[GROUP DEBUG] 添加到组: ({cx},{cy}), 当前组大小: {len(group)}")

            # 添加相邻位置
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in group:
                    stack.append((nx, ny))

        if debug:
            print(f"[GROUP DEBUG] 最终棋组: {group}, 大小: {len(group)}")
        return group

    def place_stone(self, x: int, y: int) -> Tuple[bool, str]:
        """落子"""
        if not self.is_valid_move(x, y):
            return False, "无效的落子位置"

        # 记录打劫状态
        old_ko = self.ko_point

        # 落子
        self.board[y][x] = self.current_player
        opponent = 3 - self.current_player

        # 检查并提子
        captured = self._find_and_capture_stones(x, y, opponent)

        # 更新提子统计
        if captured:
            captured_count = len(captured)
            # 注意：opponent是被提子的一方
            # 如果opponent是1(黑)，说明白棋提了黑子，白棋提子数增加
            # 如果opponent是2(白)，说明黑棋提了白子，黑棋提子数增加
            
            # 这里之前的逻辑可能有误：
            # self.captured_black 记录的是黑棋提了多少子
            # self.captured_white 记录的是白棋提了多少子
            
            if self.current_player == 1: # 当前是黑棋落子
                self.captured_black += captured_count
            else: # 当前是白棋落子
                self.captured_white += captured_count

            # 检查是否形成打劫
            if captured_count == 1:
                # 检查自己这组棋是否也只有一口气
                my_group = self._get_group_at(self.board, x, y, self.current_player)
                if self._count_liberties_of_group(self.board, my_group) == 1:
                    self.ko_point = next(iter(captured))  # 获取集合中唯一的元素
                else:
                    self.ko_point = None
            else:
                self.ko_point = None
        else:
            self.ko_point = None

        # 记录历史
        self.move_history.append({
            'x': x,
            'y': y,
            'player': self.current_player,
            'captured': len(captured)
        })
        self.last_move = (x, y)

        # 切换玩家
        self.current_player = opponent

        return True, f"落子成功，提子{len(captured)}颗"

    def _find_and_capture_stones(self, x: int, y: int, opponent: int) -> Set[Tuple[int, int]]:
        """
        查找并移除所有被提吃的棋子
        返回被提吃的棋子坐标集合

        关键修复：检查对方棋组是否有气时，必须排除当前落子位置！
        """
        all_captured = set()
        checked_groups = set()  # 使用frozenset跟踪已检查的组，防止重复处理
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        print(f"[CAPTURE DEBUG] 落子位置: ({x},{y}), 对手: {opponent}")

        # 检查四个方向的对方棋子组
        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if not (0 <= nx < self.size and 0 <= ny < self.size):
                continue

            if self.board[ny][nx] != opponent:
                continue

            # 如果这个位置的棋子已经被标记为提吃，则跳过
            if (nx, ny) in all_captured:
                print(f"[CAPTURE DEBUG] 跳过已捕获位置: ({nx},{ny})")
                continue

            # 获取这个对方棋子所在的组（启用详细调试）
            opponent_group = self._get_group_at(self.board, nx, ny, opponent, debug=True)
            print(f"[CAPTURE DEBUG] 发现棋组: {opponent_group}, 大小: {len(opponent_group)}")

            # 使用frozenset作为组的唯一ID，防止重复处理同一组
            group_id = frozenset(opponent_group)
            if group_id in checked_groups:
                print(f"[CAPTURE DEBUG] 棋组已检查过，跳过")
                continue
            checked_groups.add(group_id)

            # 关键修复：检查这个组是否有气时，排除当前落子位置(x,y)
            # 因为我们刚下的棋子占据了那个位置，对方不能利用它作为气
            has_liberty = self._group_has_liberty_excluding(self.board, opponent_group, opponent, x, y)
            print(f"[CAPTURE DEBUG] 棋组{'有' if has_liberty else '无'}气")

            if not has_liberty:
                # 这个组没有气了，全部提吃
                print(f"[CAPTURE DEBUG] 棋组将被提吃: {opponent_group}")
                all_captured.update(opponent_group)

        print(f"[CAPTURE DEBUG] 总共捕获: {len(all_captured)} 个: {all_captured}")

        # 从棋盘上移除被提吃的棋子
        for cx, cy in all_captured:
            print(f"[CAPTURE DEBUG] 移除棋子: ({cx},{cy})")
            self.board[cy][cx] = 0

        # 验证：移除后检查棋盘上是否还有该玩家的棋子
        remaining_opponent = sum(row.count(opponent) for row in self.board)
        print(f"[CAPTURE DEBUG] 移除后对手剩余棋子数: {remaining_opponent}")

        return all_captured

    def _count_liberties_of_group(self, board: List[List[int]], group: Set[Tuple[int, int]]) -> int:
        """计算棋子组的气数"""
        liberties = set()
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if board[ny][nx] == 0:
                        liberties.add((nx, ny))

        return len(liberties)

    def pass_move(self):
        """虚着"""
        self.move_history.append({
            'x': -1,
            'y': -1,
            'player': self.current_player,
            'captured': 0
        })
        self.current_player = 3 - self.current_player
        self.ko_point = None

    def get_board_state(self) -> List[List[int]]:
        """获取棋盘状态"""
        return [row[:] for row in self.board]

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """获取所有合法的落子位置"""
        valid_moves = []
        for y in range(self.size):
            for x in range(self.size):
                if self.is_valid_move(x, y):
                    valid_moves.append((x, y))
        return valid_moves

    def is_game_over(self) -> bool:
        """检查游戏是否结束（连续两次虚着）"""
        if len(self.move_history) >= 2:
            if (self.move_history[-1]['x'] == -1 and
                self.move_history[-2]['x'] == -1):
                return True
        return False

    def get_score(self) -> Tuple[int, int]:
        """
        计算分数（简化版数地法）
        返回: (黑棋分数, 白棋分数)
        """
        black_score = self.captured_black
        white_score = self.captured_white + 6.5  # 贴目

        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == 1:
                    black_score += 1
                elif self.board[y][x] == 2:
                    white_score += 1
                else:
                    # 简单的领地判断
                    territory = self._get_territory_owner(x, y)
                    if territory == 1:
                        black_score += 1
                    elif territory == 2:
                        white_score += 1

        return black_score, white_score

    def _get_territory_owner(self, x: int, y: int) -> int:
        """判断空位的归属（使用泛洪填充）"""
        if self.board[y][x] != 0:
            return 0

        visited = set()
        stack = [(x, y)]
        touches_black = False
        touches_white = False
        empty_region = set()

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            if not (0 <= cx < self.size and 0 <= cy < self.size):
                continue

            cell_value = self.board[cy][cx]

            if cell_value == 1:
                touches_black = True
            elif cell_value == 2:
                touches_white = True
            else:
                empty_region.add((cx, cy))
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    stack.append((cx + dx, cy + dy))

        if touches_black and not touches_white:
            return 1
        elif touches_white and not touches_black:
            return 2
        return 0

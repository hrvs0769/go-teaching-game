"""
DeepSeek AI引擎
使用DeepSeek API进行围棋决策分析
"""

import os
import re
import json
from typing import Tuple, List, Set
from openai import OpenAI
from .go_board import GoBoard


class DeepSeekAI:
    """基于DeepSeek API的围棋AI"""

    def __init__(self, board: GoBoard, player: int, difficulty: str = "medium"):
        self.board = board
        self.player = player  # AI执黑或执白
        self.opponent = 3 - player
        self.difficulty = difficulty

        # 初始化DeepSeek客户端
        self.client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", "sk-5a597fd91acb4c4693977dde2b0c58f2"),
            base_url="https://api.deepseek.com"
        )

    def get_move(self) -> Tuple[int, int, str]:
        """获取AI的落子决策"""
        # 获取所有合法落子位置
        valid_moves = self.board.get_valid_moves()

        if not valid_moves:
            return -1, -1, "没有合法的落子位置，选择虚着"

        try:
            # 使用DeepSeek API分析
            x, y, explanation = self._get_deepseek_move(valid_moves)
            return x, y, explanation
        except Exception as e:
            # 如果API调用失败，返回fallback解释
            print(f"DeepSeek API调用失败: {e}")
            # 使用简单的策略作为fallback
            x, y = valid_moves[0]
            return x, y, f"选择 ({x+1}, {y+1})：基础策略落子"

    def _get_deepseek_move(self, valid_moves: List[Tuple[int, int]]) -> Tuple[int, int, str]:
        """调用DeepSeek API获取落子建议"""

        # 构造棋盘状态描述
        board_description = self._describe_board()

        # 构造prompt
        prompt = f"""你是一个围棋AI助手。请分析当前棋局并给出最佳落子建议。

当前信息：
- 棋盘大小：{self.board.size}x{self.board.size}
- 你执：{'黑棋' if self.player == 1 else '白棋'}
- 当前手数：{len(self.board.move_history)}
- 难度级别：{self.difficulty}

{board_description}

请分析并给出你的落子建议，格式要求：
1. 坐标：使用(x,y)格式，x和y都是1-19的数字
2. 解释：详细说明为什么选择这个位置，包括战术分析、战略考虑等

示例输出格式：
坐标：(10,10)
解释：占据天元，控制中央，同时向四周扩展影响力...

你的分析："""

        # 调用DeepSeek API
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的围棋AI助手，精通围棋理论和战术。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        # 解析响应
        content = response.choices[0].message.content
        return self._parse_response(content, valid_moves)

    def _describe_board(self) -> str:
        """描述棋盘状态"""
        desc = []

        # 基本信息
        black_count = sum(row.count(1) for row in self.board.board)
        white_count = sum(row.count(2) for row in self.board.board)

        desc.append(f"盘面情况：")
        desc.append(f"- 黑子数量：{black_count}")
        desc.append(f"- 白子数量：{white_count}")
        desc.append(f"- 黑方提子：{self.board.captured_black}")
        desc.append(f"- 白方提子：{self.board.captured_white}")

        # 判断游戏阶段
        move_count = len(self.board.move_history)
        if move_count < 40:
            phase = "开局"
        elif move_count < 100:
            phase = "中盘"
        else:
            phase = "官子"

        desc.append(f"- 游戏阶段：{phase}")

        # 描述关键位置
        important_positions = self._find_important_positions()
        if important_positions:
            desc.append(f"\n关键位置：")
            for pos_desc in important_positions:
                desc.append(f"  - {pos_desc}")

        # 最近的落子
        if self.board.last_move:
            lx, ly = self.board.last_move
            desc.append(f"\n上一手：({lx+1}, {ly+1})")

        return "\n".join(desc)

    def _find_important_positions(self) -> List[str]:
        """寻找棋盘上的关键位置"""
        important = []

        # 寻找战斗区域（双方棋子相邻的位置）
        fought_areas = self._find_fight_areas()
        if fought_areas:
            important.append(f"战斗区域：{', '.join(f'({x+1},{y+1})' for x, y in fought_areas[:5])}")

        # 寻找处于危险中的棋组
        endangered = self._find_endangered_groups()
        if endangered:
            important.append(f"危险棋组：{endangered}")

        return important

    def _find_fight_areas(self) -> List[Tuple[int, int]]:
        """寻找战斗激烈的区域"""
        fight_areas = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.board.board[y][x] != 0:
                    # 检查周围是否有对方棋子
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                            if self.board.board[ny][nx] != 0 and self.board.board[ny][nx] != self.board.board[y][x]:
                                fight_areas.append((x, y))
                                break

        return fight_areas[:10]  # 返回最多10个战斗点

    def _find_endangered_groups(self) -> str:
        """寻找处于危险中的棋组"""
        endangered_info = []

        # 检查己方棋组
        visited = set()
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.board.board[y][x] == self.player and (x, y) not in visited:
                    group = self._get_group(x, y, self.player)
                    visited.update(group)
                    liberties = self._count_group_liberties(group)

                    if liberties <= 2:
                        group_pos = f"({x+1},{y+1})附近的{len(group)}颗子"
                        endangered_info.append(f"{group_pos}仅有{liberties}气")

        return "; ".join(endangered_info) if endangered_info else "无"

    def _get_group(self, x: int, y: int, player: int) -> Set[Tuple[int, int]]:
        """获取相连的棋子组"""
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

    def _count_group_liberties(self, group: Set[Tuple[int, int]]) -> int:
        """计算棋子组的气数"""
        liberties = set()
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for gx, gy in group:
            for dx, dy in directions:
                nx, ny = gx + dx, gy + dy
                if 0 <= nx < self.board.size and 0 <= ny < self.board.size:
                    if self.board.board[ny][nx] == 0:
                        liberties.add((nx, ny))

        return len(liberties)

    def _parse_response(self, content: str, valid_moves: List[Tuple[int, int]]) -> Tuple[int, int, str]:
        """解析DeepSeek的响应"""

        # 尝试提取坐标
        # 支持多种格式：(10,10), (10, 10), 10,10等
        coord_patterns = [
            r'坐标[：:]\s*\((\d+),\s*(\d+)\)',
            r'坐标[：:]\s*(\d+),\s*(\d+)',
            r'\((\d+),\s*(\d+)\)',
            r'选择\s*\((\d+),\s*(\d+)\)',
            r'落子\s*\((\d+),\s*(\d+)\)',
        ]

        x, y = None, None
        for pattern in coord_patterns:
            match = re.search(pattern, content)
            if match:
                x = int(match.group(1)) - 1  # 转换为0-based
                y = int(match.group(2)) - 1
                break

        # 验证坐标是否合法
        if x is not None and y is not None:
            if 0 <= x < self.board.size and 0 <= y < self.board.size:
                if (x, y) in valid_moves:
                    # 提取解释
                    explanation = self._extract_explanation(content)
                    return x, y, explanation

        # 如果无法解析或坐标不合法，使用合法的随机位置
        fallback_x, fallback_y = valid_moves[0]
        explanation = f"{content}\n\n[注：推荐的坐标不可用，已选择备用位置 ({fallback_x+1}, {fallback_y+1})]"
        return fallback_x, fallback_y, explanation

    def _extract_explanation(self, content: str) -> str:
        """提取解释部分"""
        # 移除坐标行
        lines = content.split('\n')
        explanation_lines = []

        for line in lines:
            line = line.strip()
            # 跳过坐标行
            if line.startswith('坐标') or re.match(r'^\(\d+,\s*\d+\)', line):
                continue
            if line.startswith('解释') or line.startswith('分析') or line.startswith('理由'):
                continue
            if line:
                explanation_lines.append(line)

        explanation = '\n'.join(explanation_lines).strip()

        # 如果解释为空，返回原始内容
        if not explanation:
            explanation = content

        # 添加坐标信息
        return explanation


def create_deepseek_ai(board: GoBoard, player: int, difficulty: str = "medium") -> DeepSeekAI:
    """创建DeepSeek AI实例"""
    return DeepSeekAI(board, player, difficulty)

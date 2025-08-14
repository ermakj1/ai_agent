from __future__ import annotations

import random
from typing import List, Optional, Tuple, Dict, Any

from google.genai import types

from agent import agent


class tictactoe(agent):
    def __init__(self, difficulty: str = "medium") -> None:
        super().__init__()
        self.difficulty = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
        self.board: List[List[str]] = [[" ", " ", " "] for _ in range(3)]
        self.current_player: str = "X"  # X = human, O = agent by convention
        self.status: str = "playing"  # playing | win_X | win_O | draw
        self.winner: Optional[str] = None

        self.system_prompt = (
            """
You are a Tic-Tac-Toe game agent. Maintain the game state and play against the user.

Conventions:
- Board indices are 0..2 for both row and col.
- Players: 'X' (user) and 'O' (agent).
- Validate every move. Reject invalid moves (out of bounds or occupied) with a clear message.
- Always check for win/draw after each move and report status.

Use the available functions to:
- print_board(): Show the current board state.
- ask_user_move(): Ask the human to choose a legal move for 'X'.
- make_move(row?, col?, player?): Make a move for the specified player. If player='O' and row/col are omitted, the agent must choose a move according to difficulty (easy|medium|hard).

Return concise JSON-like results describing updates (board, last_move, status, winner, next_player).
"""
        )

        # Expose tool functions
        self.available_functions = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="print_board",
                    description="Print the current Tic-Tac-Toe board.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={},
                    ),
                ),
                types.FunctionDeclaration(
                    name="ask_user_move",
                    description="Ask the user to make a legal move as 'X' and list legal coordinates.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={},
                    ),
                ),
                types.FunctionDeclaration(
                    name="make_move",
                    description=(
                        "Make a move for the specified player. If player='O' (agent) and row/col are omitted, the agent chooses a move based on difficulty."
                    ),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "row": types.Schema(type=types.Type.INTEGER, description="Row index 0..2", nullable=True),
                            "col": types.Schema(type=types.Type.INTEGER, description="Col index 0..2", nullable=True),
                            "player": types.Schema(type=types.Type.STRING, description="'X' for user, 'O' for agent", enum=["X", "O"], nullable=True),
                        },
                    ),
                ),
            ]
        )

    # Public API used by main dispatcher
    def handle_function(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "print_board":
            return {"board": self._board_str(), "status": self.status, "winner": self.winner}
        if name == "ask_user_move":
            return {
                "message": "Your turn as 'X'. Provide row and col (0..2).",
                "legal_moves": self._legal_moves(),
                "board": self._board_str(),
                "status": self.status,
            }
        if name == "make_move":
            row = args.get("row")
            col = args.get("col")
            player = args.get("player") or self.current_player
            result = self._make_move(player, row, col)
            return result
        raise ValueError(f"Unknown tictactoe function: {name}")

    # Game logic
    def _make_move(self, player: str, row: Optional[int], col: Optional[int]) -> Dict[str, Any]:
        if self.status != "playing":
            return {"error": f"Game over: {self.status}", "board": self._board_str(), "status": self.status, "winner": self.winner}

        if player not in ("X", "O"):
            return {"error": "Invalid player. Use 'X' or 'O'."}

        if player == "O" and (row is None or col is None):
            row, col = self._choose_agent_move()

        if not self._is_valid_move(row, col):
            return {"error": "Invalid move. Use 0..2 for row/col and pick an empty cell.", "legal_moves": self._legal_moves(), "board": self._board_str()}

        self.board[row][col] = player
        self.current_player = "O" if player == "X" else "X"
        self._update_status()
        return {
            "board": self._board_str(),
            "last_move": {"row": row, "col": col, "player": player},
            "status": self.status,
            "winner": self.winner,
            "next_player": self.current_player,
        }

    def _is_valid_move(self, row: Optional[int], col: Optional[int]) -> bool:
        if row is None or col is None:
            return False
        if not (0 <= row <= 2 and 0 <= col <= 2):
            return False
        return self.board[row][col] == " "

    def _legal_moves(self) -> List[Tuple[int, int]]:
        return [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == " "]

    def _board_str(self) -> str:
        rows = [" | ".join(self.board[r]) for r in range(3)]
        return f"\n{rows[0]}\n- + - + -\n{rows[1]}\n- + - + -\n{rows[2]}\n"

    def _update_status(self) -> None:
        lines = []
        b = self.board
        # rows, cols
        lines.extend(b)
        lines.extend([[b[0][i], b[1][i], b[2][i]] for i in range(3)])
        # diagonals
        lines.append([b[0][0], b[1][1], b[2][2]])
        lines.append([b[0][2], b[1][1], b[2][0]])
        for line in lines:
            if line[0] != " " and line[0] == line[1] == line[2]:
                self.status = f"win_{line[0]}"
                self.winner = line[0]
                return
        if all(b[r][c] != " " for r in range(3) for c in range(3)):
            self.status = "draw"
            self.winner = None
        else:
            self.status = "playing"
            self.winner = None

    # Agent move selection
    def _choose_agent_move(self) -> Tuple[int, int]:
        legal = self._legal_moves()
        if not legal:
            return 0, 0
        if self.difficulty == "easy":
            return random.choice(legal)
        if self.difficulty == "medium":
            move = self._winning_move("O") or self._winning_move("X")
            return move if move else random.choice(legal)
        # hard = minimax
        score, move = self._minimax_best_move("O")
        return move if move else random.choice(legal)

    def _winning_move(self, player: str) -> Optional[Tuple[int, int]]:
        for r, c in self._legal_moves():
            self.board[r][c] = player
            self._update_status()
            won = self.status == f"win_{player}"
            self.board[r][c] = " "  # revert
            self._update_status()
            if won:
                return (r, c)
        return None

    def _minimax_best_move(self, player: str) -> Tuple[int, Optional[Tuple[int, int]]]:
        opponent = "X" if player == "O" else "O"
        if self.status.startswith("win_"):
            return (1 if self.winner == "O" else -1, None)
        if self.status == "draw" or not self._legal_moves():
            return (0, None)

        best_score = -10 if player == "O" else 10
        best_move: Optional[Tuple[int, int]] = None

        for r, c in self._legal_moves():
            self.board[r][c] = player
            prev_status, prev_winner = self.status, self.winner
            self._update_status()
            score, _ = self._minimax_best_move(opponent)
            # undo
            self.board[r][c] = " "
            self.status, self.winner = prev_status, prev_winner

            if player == "O":
                if score > best_score:
                    best_score, best_move = score, (r, c)
            else:
                if score < best_score:
                    best_score, best_move = score, (r, c)

        return best_score, best_move

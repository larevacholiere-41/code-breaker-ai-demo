from asyncio import Queue
from enum import Enum
from random import sample
import uuid
from pydantic import BaseModel
from typing import Any, AsyncGenerator
from evaluation_function import evaluate_guess_simplified


class Player(str, Enum):
    PLAYER_1 = "player_1"
    PLAYER_2 = "player_2"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Guess(BaseModel):
    code: str
    feedback: int
    comments: str | None
    player: Player


class GameState(BaseModel):
    game_id: str
    status: GameStatus
    game_queue_id: str
    waiting_for_player: Player | None
    winner: Player | None
    player_1_secret_code: str
    player_2_secret_code: str
    history: list[Guess] = list()
    buffer: dict[Player, list[Guess]] = {Player.PLAYER_1: list(), Player.PLAYER_2: list()}


class QueueManager:

    def __init__(self):
        self.queues: dict[str, Queue[GameState]] = {}

    def get_queue(self, game_id: str) -> Queue[GameState]:
        if game_id not in self.queues:
            self.queues[game_id] = Queue[GameState]()
        return self.queues[game_id]


class GameEngine:

    def __init__(self):
        self.games: dict[str, GameState] = {}
        self.queue_manager = QueueManager()

    async def evaluate_guess(self, guess: str, secret: str) -> int:
        return evaluate_guess_simplified(guess, secret)

    async def create_game(self, secrets: tuple[str | None, str | None]) -> GameState:
        game_id = str(uuid.uuid4())
        secret_1 = secrets[0] or "".join(str(digit) for digit in sample(range(10), 4))
        secret_2 = secrets[1] or "".join(str(digit) for digit in sample(range(10), 4))

        game_state = GameState(
            game_id=game_id, status=GameStatus.IN_PROGRESS, game_queue_id=str(uuid.uuid4()),
            waiting_for_player=Player.PLAYER_1, winner=None, player_1_secret_code=secret_1,
            player_2_secret_code=secret_2, history=[])

        self.games[game_id] = game_state
        return game_state

    async def listen_for_updates(self, game_id: str) -> AsyncGenerator[GameState, Any]:
        queue = self.queue_manager.get_queue(game_id)
        state = self.games[game_id]
        yield state
        while state.status != GameStatus.COMPLETED:
            state = await queue.get()
            yield state

    async def process_guess(self, game_id: str, guess: Guess) -> None:
        game_state = self.games[game_id]
        feedback = await self.evaluate_guess(
            guess.code, game_state.player_2_secret_code if game_state.waiting_for_player
            == Player.PLAYER_1 else game_state.player_1_secret_code)
        guess.feedback = feedback
        game_state.history.append(guess)
        game_state.waiting_for_player = (
            Player.PLAYER_2 if guess.player == Player.PLAYER_1 else Player.PLAYER_1)
        if feedback == 4:
            game_state.status = GameStatus.COMPLETED
            game_state.winner = guess.player
        await self.queue_manager.get_queue(game_id).put(game_state.model_copy())

    async def process_buffer(self, game_id: str) -> None:
        game_state = self.games[game_id]

        if game_state.waiting_for_player is None:
            raise ValueError("Game is not in progress")

        player_buffer = game_state.buffer[game_state.waiting_for_player]

        while len(player_buffer) > 0:
            guess = player_buffer.pop(0)

            await self.process_guess(game_id, guess)
            player_buffer = game_state.buffer[game_state.waiting_for_player]

    async def make_guess(
            self, game_id: str, guess: str, player: Player, comments: str | None = None) -> None:
        game_state = self.games[game_id]

        game_state.buffer[player].append(
            Guess(code=guess, feedback=0, comments=comments, player=player))
        await self.process_buffer(game_id)

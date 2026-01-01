from asyncio import Queue
from enum import Enum
from random import sample
import uuid
from pydantic import BaseModel
from typing import Any, AsyncGenerator
from time import time
from evaluation_function import evaluate_guess_simplified

from config import Config, ConfigProvider
from logger_provider import LoggerProvider

log = LoggerProvider.get_logger('game_engine')


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
    created_at: float
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
        self.queues: dict[str, set[Queue[GameState]]] = {}

    def create_queue(self, game_id: str) -> Queue[GameState]:
        log.info(f"Creating queue for game: {game_id}")
        queue = Queue[GameState]()
        if game_id not in self.queues:
            self.queues[game_id] = set()
        self.queues[game_id].add(queue)
        return queue

    def remove_queue(self, queue: Queue[GameState]) -> None:
        log.info(f"Removing queue: {queue}")
        for game_id, queues in self.queues.items():
            if queue in queues:
                log.info(f"Removing queue: {queue} from game: {game_id}")
                queues.discard(queue)
            if len(queues) == 0:
                log.info(f"Removing game: {game_id} from queues")
                self.queues.pop(game_id)
                break


class GameEngine:

    def __init__(self, config: Config = ConfigProvider.get_config()):
        self.games: dict[str, GameState] = {}
        self.queue_manager = QueueManager()
        self.config = config

    async def evaluate_guess(self, guess: str, secret: str) -> int:
        log.info(f"Evaluating guess: {guess} for secret: {secret}")
        return evaluate_guess_simplified(guess, secret)

    async def create_game(self, secrets: tuple[str | None, str | None]) -> GameState:
        game_id = str(uuid.uuid4())
        log.info(f"Creating game with secrets: {secrets}")
        secret_1 = secrets[0] or "".join(str(digit) for digit in sample(range(10), 4))
        secret_2 = secrets[1] or "".join(str(digit) for digit in sample(range(10), 4))

        log.info(f"Game created with secrets: {secret_1} and {secret_2}")

        game_state = GameState(
            game_id=game_id, created_at=time(), status=GameStatus.IN_PROGRESS,
            game_queue_id=str(uuid.uuid4()), waiting_for_player=Player.PLAYER_1, winner=None,
            player_1_secret_code=secret_1, player_2_secret_code=secret_2, history=[])

        self.games[game_id] = game_state
        log.info(f"Game created with id: {game_id}")
        return game_state

    async def listen_for_updates(self, game_id: str) -> AsyncGenerator[GameState, Any]:
        queue = self.queue_manager.create_queue(game_id)
        state = self.games[game_id]
        log.info(f"Listening for updates for game: {game_id}")
        yield state
        while state.status != GameStatus.COMPLETED:
            state = await queue.get()
            log.info(f"Received update for game: {game_id}")
            yield state
        log.info(f"Game completed: {game_id}")
        self.queue_manager.remove_queue(queue)

    async def publish_update(self, game_id: str, state: GameState) -> None:
        log.info(f"Publishing update for game: {game_id}")
        for queue in self.queue_manager.queues.get(game_id, set()):
            await queue.put(state)

    async def process_guess(self, game_id: str, guess: Guess) -> None:
        game_state = self.games[game_id]
        log.info(f"Processing guess: {guess} for game: {game_id}")
        feedback = await self.evaluate_guess(
            guess.code, game_state.player_2_secret_code if game_state.waiting_for_player
            == Player.PLAYER_1 else game_state.player_1_secret_code)
        log.info(f"Feedback: {feedback}")
        guess.feedback = feedback
        game_state.history.append(guess)
        game_state.waiting_for_player = (
            Player.PLAYER_2 if guess.player == Player.PLAYER_1 else Player.PLAYER_1)
        if feedback == 4:
            game_state.status = GameStatus.COMPLETED
            game_state.winner = guess.player
        await self.publish_update(game_id, game_state.model_copy())

    async def process_buffer(self, game_id: str) -> None:
        log.info('processing buffer for game: {game_id}')
        game_state = self.games[game_id]

        if game_state.waiting_for_player is None:
            log.error(f"Game is not in progress: {game_id}")
            raise ValueError("Game is not in progress")

        player_buffer = game_state.buffer[game_state.waiting_for_player]
        log.info(f"Player buffer: {player_buffer}")

        while len(player_buffer) > 0:
            guess = player_buffer.pop(0)
            log.info(f"Processing guess: {guess}")
            await self.process_guess(game_id, guess)
            player_buffer = game_state.buffer[game_state.waiting_for_player]
            log.info(f"Player buffer: {player_buffer}")

    async def make_guess(
            self, game_id: str, guess: str, player: Player, comments: str | None = None) -> None:
        log.info(f"Making guess: {guess} for player: {player} for game: {game_id}")
        game_state = self.games[game_id]

        game_state.buffer[player].append(
            Guess(code=guess, feedback=0, comments=comments, player=player))
        await self.process_buffer(game_id)

    async def cleanup_games(self) -> None:
        for game_id, game_state in self.games.items():
            if game_state.created_at + self.config.GAME_ENGINE_GAME_TIMEOUT < time():
                log.info(f"Cleaning up game: {game_id}")
                self.games.pop(game_id)

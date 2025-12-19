from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import StreamingResponse
from agent_protocol import IAsyncGuesser
from chains.guesser_v3 import AsyncGuesserV3
from config import ConfigProvider
from api import API
from fastapi_deps import ApiType
import uvicorn

from game_engine import GameStatus, Player

config = ConfigProvider.get_config()


@asynccontextmanager
async def lifespan(_: FastAPI):
    api = API()
    yield {'core_api': api}


middleware = [
    Middleware(
        CORSMiddleware,
        allow_methods=["*"],
        allow_origins=["*"],
        allow_credentials=True,
        allow_headers=["*"],
    ), ]

app = FastAPI(middleware=middleware, lifespan=lifespan)


async def get_game_updates_stream(api: ApiType, game_id: str):
    ge = api.game_engine
    yield f"data: {ge.games[game_id].model_dump_json()}\n\n"
    async for state in ge.listen_for_updates(game_id):
        yield f"data: {state.model_dump_json()}\n\n"


async def start_guesser_task(api: ApiType, game_id: str, guesser: IAsyncGuesser):
    ge = api.game_engine
    max_attempts = config.GUESSER_MAX_ATTEMPTS
    game_state = ge.games[game_id]
    for attempt in range(max_attempts):
        if game_state.status == GameStatus.COMPLETED:
            break
        guess = await guesser.guess()
        if guess is None:
            break
        await ge.make_guess(game_id, guess.guess, Player.PLAYER_2, comments=guess.comments)
        feedback = await ge.evaluate_guess(guess.guess, game_state.player_1_secret_code)
        await guesser.provide_feedback((feedback, 0))


@app.post("/start-new-game-player-vs-ai")
async def start_new_game_player_vs_ai(
        api: ApiType, secret_1: str, background_tasks: BackgroundTasks):
    ge = api.game_engine
    game_id = await ge.create_game(secrets=(secret_1, None))
    guesser = AsyncGuesserV3()
    background_tasks.add_task(start_guesser_task, api, game_id.game_id, guesser)
    return {"game_id": game_id}


@app.post("/make-guess")
async def make_guess(api: ApiType, game_id: str, guess: str):
    ge = api.game_engine
    await ge.make_guess(game_id, guess, Player.PLAYER_1)
    return {"message": "Guess made successfully"}


@app.get("/get-game-updates")
async def get_game_updates(api: ApiType, game_id: str):
    return StreamingResponse(get_game_updates_stream(api, game_id), media_type="text/event-stream")


if __name__ == "__main__":
    cfg = ConfigProvider.get_config()
    uvicorn.run(
        "fastapi_server:app",
        host=cfg.FASTAPI_HOST,
        port=cfg.FASTAPI_PORT,
        reload=cfg.FASTAPI_RELOAD,
        root_path=cfg.FASTAPI_ROOT_PATH,
        access_log=True,
        log_level='debug',
    )

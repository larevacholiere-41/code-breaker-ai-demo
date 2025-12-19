import pytest
import asyncio
from game_engine import GameEngine, GameStatus, Player
from chains.guesser_v3 import AsyncGuesserV3
from logger_provider import LoggerProvider

log = LoggerProvider.get_logger('test_game_engine')


@pytest.mark.asyncio
async def test_game_engine():
    ge = GameEngine()
    game_state = await ge.create_game(secrets=("4821", "8135"))

    async def listen_for_updates():
        async for state in ge.listen_for_updates(game_state.game_id):
            print('Received state update:')
            print(state)

    game_id = game_state.game_id
    guesses = [
        ge.make_guess(game_id, "1234", Player.PLAYER_2),
        ge.make_guess(game_id, "1234", Player.PLAYER_1),
        ge.make_guess(game_id, "8135", Player.PLAYER_1)]

    async def make_guesses():
        await asyncio.sleep(1)
        for guess in guesses:
            await guess
            print(f"Made guess: {guess}")
            await asyncio.sleep(1)

    await asyncio.gather(listen_for_updates(), make_guesses())


@pytest.mark.asyncio
async def test_game_with_guesser_v3_player_1_wins():
    MAX_ATTEMPTS = 15
    ge = GameEngine()
    game_state = await ge.create_game(secrets=("4821", "8135"))
    game_id = game_state.game_id
    guesser = AsyncGuesserV3()

    async def guesser_thread():
        error_count = 0
        for _ in range(MAX_ATTEMPTS):
            if game_state.status == GameStatus.COMPLETED:
                log.info(f"Game completed after {_ + 1} attempts")
                log.info(f"Winner: {game_state.winner}")
                log.info("Terminating guesser thread")
                break
            try:
                guess = await guesser.guess()
                log.info(f"Guesser made guess: {guess}")
            except Exception as e:
                log.error(f"Error making guess: {e}")
                error_count += 1
                if error_count > 3:
                    break
                continue

            if guess is None:
                break

            await ge.make_guess(game_id, guess.guess, Player.PLAYER_2, comments=guess.comments)
            feedback = await ge.evaluate_guess(guess.guess, game_state.player_1_secret_code)
            log.info(f"Feedback: {feedback}")
            await guesser.provide_feedback((feedback, 0))

    async def player_1_thread():
        guesses = ["1234", "5678", "1235", "1243", "8135"]

        for guess in guesses:
            await ge.make_guess(game_id, guess, Player.PLAYER_1)
            log.info(f"Player 1 made guess: {guess}")

    async def listen_for_updates():
        async for state in ge.listen_for_updates(game_id):
            log.info(f"Received state update: {state}")

    await asyncio.gather(guesser_thread(), player_1_thread(), listen_for_updates())

    assert game_state.status == GameStatus.COMPLETED
    assert game_state.winner == Player.PLAYER_1


@pytest.mark.asyncio
async def test_game_with_guesser_v3_player_2_wins():
    MAX_ATTEMPTS = 15
    ge = GameEngine()
    game_state = await ge.create_game(secrets=("4821", "8135"))
    game_id = game_state.game_id
    guesser = AsyncGuesserV3()

    async def guesser_thread():
        error_count = 0
        for _ in range(MAX_ATTEMPTS):
            if game_state.status == GameStatus.COMPLETED:
                log.info(f"Game completed after {_ + 1} attempts")
                log.info(f"Winner: {game_state.winner}")
                log.info("Terminating guesser thread")
                break
            try:
                guess = await guesser.guess()
                log.info(f"Guesser made guess: {guess}")
            except Exception as e:
                log.error(f"Error making guess: {e}")
                error_count += 1
                if error_count > 3:
                    break
                continue

            if guess is None:
                break

            await ge.make_guess(game_id, guess.guess, Player.PLAYER_2, comments=guess.comments)
            feedback = await ge.evaluate_guess(guess.guess, game_state.player_1_secret_code)
            log.info(f"Feedback: {feedback}")
            await guesser.provide_feedback((feedback, 0))

    async def player_1_thread():
        guesses = ["1234", "5678", "1235", "1243", "4321", "4821", "8134", "8136", "8137", "8135"]

        for guess in guesses:
            await ge.make_guess(game_id, guess, Player.PLAYER_1)
            log.info(f"Player 1 made guess: {guess}")

    async def listen_for_updates():
        async for state in ge.listen_for_updates(game_id):
            log.info(f"Received state update: {state}")

    await asyncio.gather(guesser_thread(), player_1_thread(), listen_for_updates())

    assert game_state.status == GameStatus.COMPLETED
    assert game_state.winner == Player.PLAYER_2

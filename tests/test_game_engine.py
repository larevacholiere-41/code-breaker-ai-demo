import pytest
import asyncio
from game_engine import GameEngine, GameStatus, Player
from chains.guesser_v3 import AsyncGuesserV3
from logger_provider import LoggerProvider

log = LoggerProvider.get_logger('test_game_engine')


@pytest.mark.asyncio
async def test_game_engine_feedback():
    ge = GameEngine()
    game_state = await ge.create_game(secrets=("4821", "8135"))
    game_id = game_state.game_id

    player_1_guesses = ["1234", "5678", "1235", "1243", "8135"]
    player_1_expected_feedback = [2, 2, 3, 2, 4]
    player_2_guesses = ["1234", "5678", "1235", "1243", "8135"]

    for p1_guess, p2_guess in zip(player_1_guesses, player_2_guesses):
        await ge.make_guess(game_id, p1_guess, Player.PLAYER_1)
        await ge.make_guess(game_id, p2_guess, Player.PLAYER_2)

    player_1_feedback_list = [h.feedback for h in game_state.history if h.player == Player.PLAYER_1]

    for feedback, expected_feedback in zip(player_1_feedback_list, player_1_expected_feedback):
        assert feedback == expected_feedback


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


@pytest.mark.asyncio
async def test_multiple_update_listeners():
    """Test that multiple listeners for the same game receive all updates."""
    ge = GameEngine()
    game_state = await ge.create_game(secrets=("4821", "8135"))
    game_id = game_state.game_id

    # Lists to collect updates from each listener
    listener_1_updates = []
    listener_2_updates = []

    # Set up two listeners
    async def listener_1():
        try:
            async for state in ge.listen_for_updates(game_id):
                listener_1_updates.append(state)
                log.info(f"Listener 1 received update, status: {state.status}")
                # Break when game is completed
                if state.status == GameStatus.COMPLETED:
                    break
        except Exception as e:
            log.error(f"Listener 1 error: {e}")
            raise

    async def listener_2():
        try:
            async for state in ge.listen_for_updates(game_id):
                listener_2_updates.append(state)
                log.info(f"Listener 2 received update: {state}")
                # Break when game is completed
                if state.status == GameStatus.COMPLETED:
                    break
        except Exception as e:
            log.error(f"Listener 2 error: {e}")
            raise

    # Make guesses that will trigger updates
    guesses = [
        ("1234", Player.PLAYER_1),
        ("5678", Player.PLAYER_2),
        ("1235", Player.PLAYER_1),
        ("1243", Player.PLAYER_2),
        ("8135", Player.PLAYER_1),  # This should complete the game
    ]

    listener_1_task = asyncio.wait_for(listener_1(), timeout=10)
    listener_2_task = asyncio.wait_for(listener_2(), timeout=10)

    async def make_guesses():
        # Small delay to ensure listeners are set up
        await asyncio.sleep(0.1)
        for guess, player in guesses:
            log.info(f"Making guess: {guess} for player: {player}")
            await ge.make_guess(game_id, guess, player)
            await asyncio.sleep(0.1)  # Small delay between guesses

    # Run all tasks concurrently
    try:
        await asyncio.gather(listener_1_task, listener_2_task, make_guesses())
    except asyncio.TimeoutError as e:
        log.error(f"Timeout error: {e}, Listener processes did not complete in time")
        log.error(f"Listener 1 updates: {listener_1_updates}")
        log.error(f"Listener 2 updates: {listener_2_updates}")
        raise

    # Both listeners should receive the initial state
    assert len(listener_1_updates) > 0, "Listener 1 should receive at least the initial state"
    assert len(listener_2_updates) > 0, "Listener 2 should receive at least the initial state"

    # Both listeners should receive the same number of updates
    assert len(listener_1_updates) == len(listener_2_updates), \
        f"Both listeners should receive the same number of updates. " \
        f"Listener 1: {len(listener_1_updates)}, Listener 2: {len(listener_2_updates)}"

    # Verify that both listeners received updates for all guesses
    # Each guess should result in an update (initial state + updates for each guess)
    expected_min_updates = 1 + len(guesses)  # Initial state + one update per guess
    assert len(listener_1_updates) >= expected_min_updates, \
        f"Listener 1 should receive at least {expected_min_updates} updates, " \
        f"but received {len(listener_1_updates)}"
    assert len(listener_2_updates) >= expected_min_updates, \
        f"Listener 2 should receive at least {expected_min_updates} updates, " \
        f"but received {len(listener_2_updates)}"

    # Verify that both listeners see the final completed state
    assert listener_1_updates[-1].status == GameStatus.COMPLETED, \
        "Listener 1 should receive the completed state"
    assert listener_2_updates[-1].status == GameStatus.COMPLETED, \
        "Listener 2 should receive the completed state"

    # Verify that both listeners see the same winner
    assert listener_1_updates[-1].winner == listener_2_updates[-1].winner, \
        "Both listeners should see the same winner"

    # Verify that the history length matches expectations
    # Each guess adds one entry to history
    final_history_length = len(listener_1_updates[-1].history)
    assert final_history_length == len(guesses), \
        f"Expected {len(guesses)} guesses in history, but found {final_history_length}"

    # Verify that both listeners have the same history length
    assert len(listener_1_updates[-1].history) == len(listener_2_updates[-1].history), \
        "Both listeners should see the same history length"

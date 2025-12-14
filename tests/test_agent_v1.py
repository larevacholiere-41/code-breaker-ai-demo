from chains.guesser_v1 import GuesserV1
from tests.agent_test_runner import test_agent, test_agent_simplified

MAX_ATTEMPTS = 20


def test_guesser_v1_with_history():
    """Test GuesserV1 agent with the test runner."""
    guesser = GuesserV1()
    success, attempts = test_agent(guesser, max_attempts=MAX_ATTEMPTS)
    # with 20 attempts, the agent seems to be unlikely to win
    return success, attempts


def test_guesser_v1_simplified():
    """Test GuesserV1 agent with simplified game (find all 4 numbers irrelevant of positions)."""
    guesser = GuesserV1()
    success, attempts = test_agent_simplified(guesser, max_attempts=MAX_ATTEMPTS)
    return success, attempts

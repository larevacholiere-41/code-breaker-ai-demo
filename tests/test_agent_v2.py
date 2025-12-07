from chains.guesser_v2 import GuesserV2
from tests.agent_test_runner import test_agent

MAX_ATTEMPTS = 20


def test_guesser_v2_with_history():
    """Test GuesserV1 agent with the test runner."""
    guesser = GuesserV2()
    success, attempts = test_agent(guesser, max_attempts=MAX_ATTEMPTS)
    # with 20 attempts, the agent seems to be unlikely to win
    return success, attempts

from chains.guesser_v3 import GuesserV3
from tests.agent_test_runner import test_agent, test_agent_simplified

MAX_ATTEMPTS = 20


def test_guesser_v3_with_history():
    """Test GuesserV1 agent with the test runner."""
    guesser = GuesserV3()
    success, attempts = test_agent_simplified(guesser, max_attempts=MAX_ATTEMPTS)
    # with 20 attempts, the agent seems to be unlikely to win
    return success, attempts

from datetime import datetime
from random import sample
from chains.guesser_v3 import GuesserV3
from tests.agent_test_runner import test_agent_simplified

MAX_ATTEMPTS = 20


def test_guesser_v3_with_history():
    """Test GuesserV1 agent with the test runner."""
    test_model = "gpt-5-nano"
    guesser = GuesserV3(model=test_model)
    success, attempts = test_agent_simplified(guesser, max_attempts=MAX_ATTEMPTS)
    # with 20 attempts, the agent seems to be unlikely to win
    return success, attempts


def test_guesser_v3_multiple_models():
    """Test GuesserV3 agent with multiple models."""
    test_models = ["gpt-5"]
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"Secret code: {secret_code}")
    results = []
    for model in test_models:
        t1 = datetime.now()
        guesser = GuesserV3(model=model)
        try:
            success, attempts = test_agent_simplified(
                guesser, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        except Exception as e:
            success = False
            attempts = None
            print(f"Error testing {model}: {e}")
        t2 = datetime.now()
        results.append((model, success, attempts, (t2 - t1).total_seconds()))
    print(f"Results: {results}")
    return results

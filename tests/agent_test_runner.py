from agent_protocol import IGuesser
from evaluation_function import evaluate_guess, evaluate_guess_simplified
from logger_provider import LoggerProvider
from random import sample

logger = LoggerProvider.get_logger('agent_test_runner')


def test_agent(agent: IGuesser, secret_code: str | None = None,
               max_attempts: int = 20) -> tuple[bool, int]:
    """
    Test an agent by having it guess a secret code.
    
    Args:
        agent: The agent to test (must implement Agent protocol)
        secret_code: The secret code to guess. If None, a random code is generated.
        max_attempts: Maximum number of attempts the agent can make.
    
    Returns:
        A tuple of (success: bool, attempts: int) indicating whether the agent
        succeeded and how many attempts were made.
    """
    if secret_code is None:
        secret_code = "".join(str(digit) for digit in sample(range(10), 4))

    logger.info(f"Secret code: {secret_code}")
    logger.info(f"Max attempts: {max_attempts}")

    for attempt in range(max_attempts):
        guess = agent.guess()
        logger.info(f"Attempt {attempt + 1}: Guess: {guess}")

        if guess is None:
            logger.error("Agent did not return a guess")
            return False, attempt + 1

        feedback = evaluate_guess(guess.guess, secret_code)
        agent.provide_feedback(feedback)
        logger.info(f"Feedback: {feedback}")

        is_won = guess.guess == secret_code
        if is_won:
            logger.info(f"Agent won after {attempt + 1} attempts!")
            return True, attempt + 1

    logger.info(f"Agent lost after {max_attempts} attempts!")
    return False, max_attempts


def test_agent_simplified(agent: IGuesser, secret_code: str | None = None,
                          max_attempts: int = 20) -> tuple[bool, int]:
    """
    Test an agent by having it guess a secret code.
    """
    if secret_code is None:
        secret_code = "".join(str(digit) for digit in sample(range(10), 4))

    logger.info(f"Secret code: {secret_code}")
    logger.info(f"Max attempts: {max_attempts}")

    for attempt in range(max_attempts):
        guess = agent.guess()
        logger.info(f"Attempt {attempt + 1}: Guess: {guess}")

        if guess is None:
            logger.error("Agent did not return a guess")
            return False, attempt + 1

        feedback = evaluate_guess_simplified(guess.guess, secret_code)
        # modified feedback for compatibility with the agent protocol
        mod_feedback = (feedback, 0)
        agent.provide_feedback(mod_feedback)
        is_won = feedback == 4
        logger.info(f"Feedback: {mod_feedback}")
        logger.info(f"Is won: {is_won}")
        if is_won:
            logger.info(f"Agent won after {attempt + 1} attempts!")
            return True, attempt + 1

    logger.info(f"Agent lost after {max_attempts} attempts!")
    return False, max_attempts

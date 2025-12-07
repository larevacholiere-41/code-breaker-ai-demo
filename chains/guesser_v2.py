from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from config import ConfigProvider
from langchain.agents import create_agent
from agent_protocol import GuessResponse
from logger_provider import LoggerProvider

logger = LoggerProvider.get_logger('guesser_v2')

SYSTEM_PROMPT = """
You are a guesser in a game of Code Breaker.
Your goal is to guess a secret code of 4 unique digits in as few attempts as possible.
You can only guess 4 digits at a time.
You can only guess digits from 0 to 9.
Your guess cannot contain duplicate digits.

STRATEGY:
- Analyze the history of your guesses and feedback to determine for each possible digit:
    - whether it MUST be in the secret code
    - whether it MAY be in the secret code
    - whether it MUST NOT be in the secret code
- Based on your analysis, decide what guess can extract the most information
  about the secret code, aim to either eliminate any digits or confirm their presence.
- By taking a sum of the two numbers in the feedback, you can determine the total number of
  digits that are present in the secret code.
- Keep in mind that you are not allowed to include duplicate digits in your guess.
- When making a guess try to predict what are the possible outcomes of your guess and 
what would it tell you about the secret code.

EXAMPLES:
Example 1:
- History: [('0123', (0, 1)), ('4567', (2, 1)))]
- Analysis:
    - The range 0-7 contains all four digits, so we can eliminate the digits 8 and 9.
- Reasoning:
    - I can combine digits from 0-3 with eliminated digits 8 and 9 to 
    gather more information about the secret code.
    - I will switch the positions of the digits from the previous guess
    to maximize the information extraction.
    - This will result one of the following outcomes:
       - (0, 0) - no digits are correct, so I will be able to eliminate 0 and 1
       - (0, 1) - one digit is correct, combining it with the first guess, 
       I will be able to eliminate 2 and 3
       - (1, 0) - one digit is correct and in the correct position, similar to the first guess
- Guess: 8901

Example 2:
- History: [('0123', (0, 1)), ('4567', (2, 1)), ('8901', (0, 1)))]
- Analysis:
    - The range 0-7 contains all four digits, so we can eliminate the digits 8 and 9.
- Reasoning:
    - I can combine digits from 0-3 with eliminated digits 8 and 9 to 
    gather more information about the secret code.
    - I will switch the positions of the digits from the previous guess
    to maximize the information extraction.
"""

MESSAGE_TEMPLATE = """
Given the following context provide your next guess.

Context:
- Guess count: {guess_count}
- History: {history}

Your next guess:
"""


class GuesserV2Response(BaseModel):
    """Response model for guesser v2."""
    analysis: str = Field(description="Your analysis based on the history (if any)")
    guess: str = Field(description="Your next guess. ")


class Memory(BaseModel):
    """Memory for the guesser v2."""
    guess_count: int = Field(default=0)
    history: list[tuple[str, tuple[int, int]]] = Field(
        default_factory=list, description="History of all previous guesses and feedback. \
            The first element is the guess, the second element is a tuple of two numbers: \
            first is the number of digits that are correct AND in the correct position, \
            second is the number of digits that are correct BUT in the wrong position.")


class GuesserV2:
    """
    GuesserV2 is a class that implements the Guesser interface.
    It uses a LangChain agent to generate guesses and provide feedback.
    Uses a more sophisticated approach to provide better performance.
    """

    def __init__(self):
        self.config = ConfigProvider.get_config()
        self.memory = Memory()
        self.agent = create_agent(
            self.config.BASE_MODEL, system_prompt=SYSTEM_PROMPT, response_format=GuesserV2Response)
        self.last_guess: GuesserV2Response | None = None

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        self.memory.history.append((self.last_guess.guess, feedback))
        logger.info(f"Feedback: {feedback}")

    def guess(self) -> GuessResponse | None:
        logger.info(f"Guessing round {self.memory.guess_count}")
        prompt = ChatPromptTemplate.from_template(MESSAGE_TEMPLATE)
        chain = prompt | self.agent
        response = chain.invoke(self.memory.model_dump())
        # update memory
        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV2Response)
        self.last_guess = structured_response
        self.memory.guess_count += 1
        logger.info(f"Guess: {structured_response.guess}")
        logger.info(f"Analysis: {structured_response.analysis}")
        guess = GuessResponse.model_validate(structured_response.model_dump())
        return guess

from langchain_core.messages import HumanMessage
from config import ConfigProvider
from langchain.agents import create_agent
from agent_protocol import GuessResponse

SYSTEM_PROMPT = """
You are a guesser in a game of Code Breaker.
Your goal is to guess all 4 digits from a secret code irrespective of the order of the digits
 and in as little attempts as possible.
You can only guess 4 digits at a time.
You can only guess digits from 0 to 9.
Your guess cannot contain duplicate digits.
For each guess you will receive feedback in the following format:
  Number <previous_guess> has <number_of_correct_digits> correct digits
"""


class GuesserV1:
    """
    GuesserV1 is a class that implements the Guesser interface.
    It uses a LangChain agent to generate guesses and provide feedback.
    Uses the simplest approach to provide baseline performance.
    """

    def __init__(self):
        self.config = ConfigProvider.get_config()
        self.chat_history: list = [HumanMessage(content="Provide your next guess.")]
        self.agent = create_agent(
            self.config.BASE_MODEL, system_prompt=SYSTEM_PROMPT, response_format=GuessResponse)
        self.previous_guess = None

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        feedback_str = f"Number {self.previous_guess} has \
            {feedback[0] + feedback[1]} correct digits"

        self.chat_history.append(HumanMessage(content=feedback_str))

    def guess(self) -> GuessResponse | None:
        response = self.agent.invoke({"messages": self.chat_history})
        structured_response = response.get("structured_response")
        if structured_response is not None:
            self.previous_guess = structured_response.guess
        messages = response.get("messages")
        if messages is not None:
            self.chat_history.append(messages[-1])
        return structured_response


class AsyncGuesserV1:
    """
    AsyncGuesserV1 is an async version of GuesserV1.
    It uses a LangChain agent to generate guesses and provide feedback asynchronously.
    """

    def __init__(self):
        self.config = ConfigProvider.get_config()
        self.chat_history: list = [HumanMessage(content="Provide your next guess.")]
        self.agent = create_agent(
            self.config.BASE_MODEL, system_prompt=SYSTEM_PROMPT, response_format=GuessResponse)
        self.previous_guess = None

    async def provide_feedback(self, feedback: tuple[int, int]) -> None:
        feedback_str = f"Number {self.previous_guess} has \
            {feedback[0] + feedback[1]} correct digits"

        self.chat_history.append(HumanMessage(content=feedback_str))

    async def guess(self) -> GuessResponse | None:
        response = await self.agent.ainvoke({"messages": self.chat_history})
        structured_response = response.get("structured_response")
        if structured_response is not None:
            self.previous_guess = structured_response.guess
        messages = response.get("messages")
        if messages is not None:
            self.chat_history.append(messages[-1])
        return structured_response

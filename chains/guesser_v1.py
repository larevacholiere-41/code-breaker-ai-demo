from langchain_core.messages import HumanMessage
from config import ConfigProvider
from langchain.agents import create_agent
from agent_protocol import GuessResponse

SYSTEM_PROMPT = """
You are a guesser in a game of Code Breaker.
Your goal is to guess a secret code of 4 unique digits in as little attempts as possible.
You can only guess 4 digits at a time.
You can only guess digits from 0 to 9.
Your guess cannot contain duplicate digits.
For each guess you will receive feedback containing two numbers:
- The first number is the number of digits that are correct and in the correct position.
- The second number is the number of digits that are correct but in the wrong position.
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

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        self.chat_history.append(HumanMessage(content=f"{feedback[0], feedback[1]}"))

    def guess(self) -> GuessResponse | None:
        response = self.agent.invoke({"messages": self.chat_history})
        structured_response = response.get("structured_response")
        messages = response.get("messages")
        if messages is not None:
            self.chat_history.append(messages[-1])
        return structured_response

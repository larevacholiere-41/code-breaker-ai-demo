from config import ConfigProvider

from langchain_core.prompts import (
    ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate)
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import create_agent

from agent_protocol import GuessResponse
from logger_provider import LoggerProvider
from models.guesser_v3 import State, GuesserV3Response
from prompts.guesser_v3 import SYSTEM_PROMPT, MESSAGE_PROMPT

log = LoggerProvider.get_logger('guesser_v3')

system_prompt_template = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
system_message = system_prompt_template.format(
    state_format_instructions=JsonOutputParser(pydantic_object=State).get_format_instructions())


class GuesserV3:
    """
    GuesserV3 is a class that implements the Guesser interface.
    It uses a LangChain agent to generate guesses and provide feedback.
    Uses a more sophisticated approach to provide better performance.
    """

    def __init__(self, model: str | None = None):
        self.config = ConfigProvider.get_config()
        self.state = State()
        model_name = model or self.config.BASE_MODEL
        self.agent = create_agent(model_name, response_format=GuesserV3Response)
        self.last_guess = None
        self.last_feedback = None
        self.round = 1

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        formatted_feedback = f"{self.last_guess} has {feedback[0] + feedback[1]} correct digits"
        self.last_feedback = formatted_feedback
        self.round += 1

    def guess(self) -> GuessResponse | None:
        if self.round == 1:
            log.info(f"system_message: {system_message}")
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            HumanMessagePromptTemplate.from_template(MESSAGE_PROMPT)])
        chain = prompt | self.agent
        response = chain.invoke({
            "round": self.round, "current_state": self.state.model_dump(),
            "previous_guess": self.last_guess, "feedback": self.last_feedback})
        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV3Response)
        self.state = structured_response.updated_state
        self.last_guess = structured_response.guess
        log.info(f"Round: {self.round}")
        log.info(f"Last guess: {self.last_guess}")
        log.info(f"Feedback: {self.last_feedback}")
        log.info(f"Updated state: {self.state.model_dump()}")
        log.info(f"Guess: {structured_response.guess}")
        log.info(f"Reasoning: {structured_response.reasoning}")
        return GuessResponse.model_validate(structured_response.model_dump())


class AsyncGuesserV3:
    """
    AsyncGuesserV3 is an async version of GuesserV3.
    It uses a LangChain agent to generate guesses and provide feedback asynchronously.
    """

    def __init__(self, model: str | None = None):
        self.config = ConfigProvider.get_config()
        self.state = State()
        model_name = model or self.config.BASE_MODEL
        self.agent = create_agent(model_name, response_format=GuesserV3Response)
        self.last_guess = None
        self.last_feedback = None
        self.round = 1

    async def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        formatted_feedback = f"{self.last_guess} has {feedback[0] + feedback[1]} correct digits"
        self.last_feedback = formatted_feedback
        self.round += 1

    async def guess(self, max_retries: int = 3) -> GuessResponse | None:
        if self.round == 1:
            log.info(f"system_message: {system_message}")
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            HumanMessagePromptTemplate.from_template(MESSAGE_PROMPT)])
        chain = prompt | self.agent

        for attempt in range(max_retries):
            try:
                response = await chain.ainvoke({
                    "round": self.round, "current_state": self.state.model_dump(),
                    "previous_guess": self.last_guess, "feedback": self.last_feedback})
                break
            except Exception as e:
                log.error(f"Error guessing: {e}")
                if attempt == max_retries - 1:
                    raise e
                continue

        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV3Response)
        self.state = structured_response.updated_state
        self.last_guess = structured_response.guess
        log.info(f"Round: {self.round}")
        log.info(f"Last guess: {self.last_guess}")
        log.info(f"Feedback: {self.last_feedback}")
        log.info(f"Updated state: {self.state.model_dump()}")
        log.info(f"Guess: {structured_response.guess}")
        log.info(f"Reasoning: {structured_response.reasoning}")
        return GuessResponse.model_validate({
            "guess": structured_response.guess, "comments": structured_response.comments})

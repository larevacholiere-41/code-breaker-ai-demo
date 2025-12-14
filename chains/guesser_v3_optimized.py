from config import ConfigProvider

from langchain_core.prompts import (
    ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate)
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import create_agent

from agent_protocol import GuessResponse
from logger_provider import LoggerProvider
from models.guesser_v3 import State, GuesserV3Response

log = LoggerProvider.get_logger('guesser_v3_optimized')

# Optimized shorter prompt with same strategy
OPTIMIZED_SYSTEM_PROMPT = """
# Code Breaker - Find 4 Digits

## Rules
- Secret: 4 unique digits (0-9)
- Feedback: "X has Y correct digits"

## Strategy
1. **Partition** (R1-2): Test groups (1234), (5678), deduce (09)
2. **Resolve**: Binary search within groups using control digits
3. **Submit**: Once 4 digits confirmed

## State Format
{state_format_instructions}

## Resolve Logic
- 0 matches → eliminate all
- matches = size → confirm all
- 1 of 4 → split test
- 2 of 4 → split, if even then diagonal, if still even then tiebreaker
- 3 of 4 → split test (find which to eliminate)

Always use confirmed/eliminated digits as controls.
"""

OPTIMIZED_MESSAGE_PROMPT = """Round {round}
State: {current_state}
Last: {previous_guess} → {feedback}"""

# Pre-compute prompt templates (optimization: avoid creating on each call)
system_prompt_template = SystemMessagePromptTemplate.from_template(OPTIMIZED_SYSTEM_PROMPT)
_cached_system_message = None


def get_system_message():
    """Cache system message for reuse."""
    global _cached_system_message
    if _cached_system_message is None:
        _cached_system_message = system_prompt_template.format(
            state_format_instructions=JsonOutputParser(
                pydantic_object=State).get_format_instructions())
    return _cached_system_message


# Pre-compute message template
_cached_prompt_template = None


def get_prompt_template():
    """Cache prompt template for reuse."""
    global _cached_prompt_template
    if _cached_prompt_template is None:
        _cached_prompt_template = ChatPromptTemplate.from_messages([
            get_system_message(),
            HumanMessagePromptTemplate.from_template(OPTIMIZED_MESSAGE_PROMPT)])
    return _cached_prompt_template


class GuesserV3Optimized:
    """
    Optimized version of GuesserV3 with reduced processing time.

    Optimizations:
    - Pre-computed and cached prompt templates
    - Minimal logging (only errors and final results)
    - Streamlined prompt (shorter but same strategy)
    - Efficient state management
    """

    def __init__(self, model: str | None = None):
        self.config = ConfigProvider.get_config()
        self.state = State()
        model_name = model or self.config.BASE_MODEL
        self.agent = create_agent(model_name, response_format=GuesserV3Response)
        self.last_guess = None
        self.last_feedback = None
        self.round = 1

        # Pre-compute chain (optimization: reuse same chain)
        self.chain = get_prompt_template() | self.agent

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        formatted_feedback = f"{self.last_guess} has {feedback[0] + feedback[1]} correct digits"
        self.last_feedback = formatted_feedback
        self.round += 1

    def guess(self) -> GuessResponse | None:
        # Use pre-computed chain
        response = self.chain.invoke({
            "round": self.round,
            "current_state": self.state.model_dump(),
            "previous_guess": self.last_guess or "None",
            "feedback": self.last_feedback or "N/A"
        })

        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV3Response)

        # Update state
        self.state = structured_response.updated_state
        self.last_guess = structured_response.guess

        # Minimal logging (only on final round or errors)
        if self.state.digits_found == 4:
            log.info(f"Completed in {self.round} rounds. Final guess: {structured_response.guess}")

        return GuessResponse.model_validate(structured_response.model_dump())


class AsyncGuesserV3Optimized:
    """
    Async optimized version of GuesserV3 with reduced processing time.

    Optimizations:
    - Pre-computed and cached prompt templates
    - Minimal logging (only errors and final results)
    - Streamlined prompt (shorter but same strategy)
    - Efficient state management
    - Async operations for better concurrency
    """

    def __init__(self, model: str | None = None):
        self.config = ConfigProvider.get_config()
        self.state = State()
        model_name = model or self.config.BASE_MODEL
        self.agent = create_agent(model_name, response_format=GuesserV3Response)
        self.last_guess = None
        self.last_feedback = None
        self.round = 1

        # Pre-compute chain (optimization: reuse same chain)
        self.chain = get_prompt_template() | self.agent

    async def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        formatted_feedback = f"{self.last_guess} has {feedback[0] + feedback[1]} correct digits"
        self.last_feedback = formatted_feedback
        self.round += 1

    async def guess(self) -> GuessResponse | None:
        # Use pre-computed chain with async invoke
        response = await self.chain.ainvoke({
            "round": self.round,
            "current_state": self.state.model_dump(),
            "previous_guess": self.last_guess or "None",
            "feedback": self.last_feedback or "N/A"
        })

        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV3Response)

        # Update state
        self.state = structured_response.updated_state
        self.last_guess = structured_response.guess

        # Minimal logging (only on final round or errors)
        if self.state.digits_found == 4:
            log.info(f"Completed in {self.round} rounds. Final guess: {structured_response.guess}")

        return GuessResponse.model_validate(structured_response.model_dump())

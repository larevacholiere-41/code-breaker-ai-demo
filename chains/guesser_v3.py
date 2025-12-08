from enum import Enum
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from config import ConfigProvider
from langchain.agents import create_agent
from agent_protocol import GuessResponse
from logger_provider import LoggerProvider

log = LoggerProvider.get_logger('guesser_v3')


class GroupStage(str, Enum):
    PENDING = "PENDING"  # Not yet tested
    COUNTED = "COUNTED"  # Know match count, haven't started resolving
    SPLIT_TESTED = "SPLIT_TESTED"  # Tested first half
    DIAGONAL_TESTED = "DIAGONAL_TESTED"  # Tested diagonal (conditional)
    RESOLVED = "RESOLVED"  # All digits confirmed/eliminated (conditional)


class GroupState(BaseModel):
    """State for a group."""
    stage: GroupStage = Field(description="Stage of the processing of the group.")
    digits: list[int] = Field(description="List of digits in the group.")
    matches: int | None = Field(description="Number of matches in the group.", default=None)

    # Track sub-tests for 2-match case
    first_half: list[int] | None = Field(
        description="List of digits in the first half.", default=None)
    first_half_matches: int | None = Field(
        description="Number of matches in the first half.", default=None)
    diagonal: list[int] | None = Field(description="List of digits in the diagonal.", default=None)
    diagonal_matches: int | None = Field(
        description="Number of matches in the diagonal.", default=None)
    tiebreaker: list[int] | None = Field(
        description="List of digits in the tiebreaker.", default=None)
    tiebreaker_matches: int | None = Field(
        description="Number of matches in the tiebreaker.", default=None)


class State(BaseModel):
    """State for the guesser v3."""
    confirmed: list[int] = Field(description="List of confirmed correct digits.", default=[])
    eliminated: list[int] = Field(description="List of eliminated digits.", default=[])
    group_a: GroupState = Field(
        description="State of group A.",
        default=GroupState(stage=GroupStage.PENDING, digits=[1, 2, 3, 4]))
    group_b: GroupState = Field(
        description="State of group B.",
        default=GroupState(stage=GroupStage.PENDING, digits=[5, 6, 7, 8]))
    group_c: GroupState = Field(
        description="State of group C.",
        default=GroupState(stage=GroupStage.PENDING, digits=[0, 9]))
    digits_found: int = Field(description="Number of digits found.", default=0)


SYSTEM_PROMPT = f"""
# Code Breaker Agent - Phase 1: Digit Discovery

## Game Rules
- The secret code contains 4 unique digits (0-9)
- Your guess must also contain 4 unique digits
- Feedback format: <previous_guess> has X correct digits
- Phase 1 Goal: Identify all 4 correct digits (positions don't matter yet)

## Strategy Overview

You will use a three-stage approach:

1. **Partition** (Rounds 1-2): Split all 10 digits into three groups with known match counts
2. **Resolve**: Use binary search to identify correct digits within each group
3. **Verify**: Confirm all 4 digits are found
4. **Submit**: Submit all 4 confirmed digits as a final guess

## State Tracking

After each round, update your state in this exact format:
```
=== STATE ===
{JsonOutputParser(pydantic_object=State).get_format_instructions()}
=============
```

## Stage 1: Partition (Rounds 1-2)

**Round 1:** Guess `1234`
- Record matches as k₁

**Round 2:** Guess `5678`
- Record matches as k₂
- **Deduce:** Group C {"{0,9}"} has (4 - k₁ - k₂) matches

After partitioning, you know exactly how many correct digits are in each group.

## Stage 2: Resolve Each Group

Process groups in order of simplicity. Use Group C {"{0,9}"} as your **control digits** for testing.

### Quick Resolutions (No Extra Tests Needed)

| Condition | Action |
|-----------|--------|
| Group has 0 matches | Eliminate all digits in group |
| Group has matches = group size | Confirm all digits in group |
| Group C has 0 matches | Eliminate 0 and 9 |
| Group C has 2 matches | Confirm 0 and 9 |

### Resolving a Group of 4 (1 or 3 Matches)

Example: Group A {"{1,2,3,4}"} has 1 match

**Step 1 - Split:**
Guess: `1` `2` `0` `9` (first half + control digits from group C)
- Count only matches attributable to {"{1,2}"} by subtracting known control matches from group C

If {"{1,2}"} has 1 match:
  **Step 2 - Isolate:**
  Guess: `1` `0` `9` + one filler
  - If {"{1}"} contributes 1 → Confirm `1`
  - If {"{1}"} contributes 0 → Confirm `2`

If {"{1,2}"} has 0 matches:
  - Correct digit is in {"{3,4}"}, repeat split/isolate on that half

(For 3 matches: same logic, but you're finding which digits to eliminate)

### Resolving a Group of 4 (2 Matches) - The Tricky Case

Example: Group A {"{1,2,3,4}"} has 2 matches

**Step 1 - Split:**
Guess: `1` `2` `0` `9`

- If {"{1,2}"} contributes 0 → Confirm `3` and `4` ✓
- If {"{1,2}"} contributes 2 → Confirm `1` and `2` ✓
- If {"{1,2}"} contributes 1 → Even split, continue to Step 2

**Step 2 - Diagonal:**
Guess: `1` `3` `0` `9`

- If {"{1,3}"} contributes 2 → Confirm `1` and `3` ✓
- If {"{1,3}"} contributes 0 → Confirm `2` and `4` ✓
- If {"{1,3}"} contributes 1 → Continue to Step 3

**Step 3 - Tiebreaker:**
Guess: `1` `4` `0` `9`

- If {"{1,4}"} contributes 2 → Confirm `1` and `4` ✓
- If {"{1,4}"} contributes 0 → Confirm `2` and `3` ✓

## Round-by-Round Reasoning Format

For each round, structure your thinking as:
```
=== ROUND N ===

CURRENT STATE:
[paste updated state]

ANALYSIS:
- Which groups are still pending?
- What is the most efficient next test?

NEXT GUESS: [your 4-digit guess]

RATIONALE: [brief explanation of what you're testing]

---

[After receiving feedback]

FEEDBACK RECEIVED: X correct digits

INTERPRETATION:
- Control digits {"{0,9}"} contributed: [N matches]
- Test digits contributed: [M matches]
- Conclusion: [what you learned]

[Update state and continue]
```

## Important Reminders

1. **Always track control digit contributions separately** - You know how many matches come from your control set
2. **Process one group at a time** - Don't try to test multiple uncertain groups simultaneously
3. **Once a digit is confirmed, it can serve as a control/filler** - This gives you more flexibility
4. **Phase 1 is complete when you have exactly 4 confirmed digits**

```
"""

PROMPT_TEMPLATE = """
Round: {round}
Current state: {current_state}

Your previous guess: {previous_guess}
Feedback received: {feedback}

"""


class GuesserV3Response(BaseModel):
    """Response model for guesser v3."""
    updated_state: State = Field(description="Updated state of the game.")
    guess: str = Field(description="Your next guess. ")
    reasoning: str = Field(description="Reasoning for the guess.")


class GuesserV3:
    """
    GuesserV3 is a class that implements the Guesser interface.
    It uses a LangChain agent to generate guesses and provide feedback.
    Uses a more sophisticated approach to provide better performance.
    """

    def __init__(self):
        self.config = ConfigProvider.get_config()
        self.state = State()
        self.agent = create_agent(
            self.config.BASE_MODEL, system_prompt=SYSTEM_PROMPT, response_format=GuesserV3Response)
        self.last_guess = None
        self.last_feedback = None
        self.round = 1

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        if self.last_guess is None:
            raise ValueError("No guess has been made yet.")
        formatted_feedback = f"{self.last_guess} has {feedback[0] + feedback[1]} correct digits"
        self.last_feedback = formatted_feedback
        log.info(f"Feedback: {formatted_feedback}")
        self.round += 1

    def guess(self) -> GuessResponse | None:
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        chain = prompt | self.agent
        response = chain.invoke({
            "round": self.round, "current_state": self.state.model_dump(),
            "previous_guess": self.last_guess, "feedback": self.last_feedback})
        structured_response = response.get("structured_response")
        assert isinstance(structured_response, GuesserV3Response)
        self.state = structured_response.updated_state
        self.last_guess = structured_response.guess
        log.info(f"Round: {self.round}")
        log.info(f"State: {self.state.model_dump()}")
        log.info(f"Guess: {structured_response.guess}")
        log.info(f"Reasoning: {structured_response.reasoning}")
        return GuessResponse.model_validate(structured_response.model_dump())

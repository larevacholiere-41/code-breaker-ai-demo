from enum import Enum
from pydantic import BaseModel, Field


class GroupStage(str, Enum):
    """Stage of processing of a group.
    Used to track the progress.
    """
    PENDING = "PENDING"
    COUNTED = "COUNTED"
    SPLIT_TESTED = "SPLIT_TESTED"
    DIAGONAL_TESTED = "DIAGONAL_TESTED"
    RESOLVED = "RESOLVED"

    @classmethod
    def get_field_description(cls) -> str:
        txt = "Stage of processing of a group. Used to track the progress."
        txt += f"\n- {cls.PENDING}: Not yet tested"
        txt += f"\n- {cls.COUNTED}: Know match count, haven't started resolving"
        txt += f"\n- {cls.SPLIT_TESTED}: Tested first half"
        txt += f"\n- {cls.DIAGONAL_TESTED}: Tested diagonal"
        txt += f"\n- {cls.RESOLVED}: All digits confirmed/eliminated"
        return txt


class GroupState(BaseModel):
    """State for a focus group."""
    stage: GroupStage = Field(description=GroupStage.get_field_description())
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


class GuesserV3Response(BaseModel):
    """Response model for guesser v3."""
    updated_state: State = Field(description="Updated state of the game.")
    guess: str = Field(description="Your next guess. ")
    reasoning: str = Field(description="Reasoning for the guess.")

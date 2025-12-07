from typing import Protocol, runtime_checkable
from pydantic import BaseModel


class GuessResponse(BaseModel):
    """Response model for agent guesses."""
    guess: str


@runtime_checkable
class IGuesser(Protocol):
    """Protocol defining the interface for Code Breaker agents."""

    def guess(self) -> GuessResponse | None:
        """
        Generate a guess for the secret code.
        
        Returns:
            GuessResponse with the guess, or None if no guess can be generated.
        """
        ...

    def provide_feedback(self, feedback: tuple[int, int]) -> None:
        """
        Provide feedback to the agent about their previous guess.
        
        Args:
            feedback: A tuple of (correct_positions, correct_numbers)
        """
        ...

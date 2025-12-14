# Progress Journal

## Jan 08, 2025

- Introduced simplified version of the game, where it is only required to find the correct digits, not the correct positions.
- Added testing suite to evaluate the performance of the guesser agent on a simplified version of the game.
- Created a guesser agent that consistently wins under 10 attempts at simplified version of the game using latest GPT-5 model.

## Dec 14, 2025

- Refactored the guesser v3 for better readability and maintainability.
- Tested the guesser v3 with multiple OpenAI models.
- Test resutls:
  - gpt-5-nano: won after 8 attempts in 237 seconds
  - gpt-5-mini: won after 7 attempts in 151 seconds
  - gpt-5: won after 7 attempts in 297 seconds
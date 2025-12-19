# TODO

## Short Term

- [x] Enable setting model version on testing, to compare performance of different models.
- [x] Explore other models to see if similar results can be achieved with smaller (faster) models.
- [x] Update testing for other guesser versions to compare performance on simplified version of the game.
- [x] Upgrade GuesserV1 and V3 to async architecture.
- [x] Create an async version of the test runner and add a test that will test V1 and V3 in parallel.
- [x] Clean up the codebase to make it more readable and maintainable.
- [x] Create a game engine for two players, enable state export for use with web UI.
- [x] Test the game engine.
- [x] Test the game engine in interactive mode with GuesserV3.
- [ ] Add validation logic to the API endpoints (mainly for the guess input).
- [ ] Add recycling logic to the game engine (game states, queues).
- [ ] Create FastAPI server to interact with GuesserV1 and V3 in interactive mode.
- [ ] RefactorGameEngine.process_buffer: move game state evaluation to a separate function.
- [ ] Add rate limiting to the API.

## Long Term

- [ ] Upgrade GuesserV3 to tackle the full version of the game.
- [ ] Create an optimized version of the guesser v3 and try to reduce the processing time.
- [ ] Create a gradio interface to test and compare the performance of the different guesser versions.

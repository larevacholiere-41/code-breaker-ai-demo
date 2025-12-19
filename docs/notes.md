# Project Notes

## Game modes

### Player vs AI

- player creates a secret code
- new game starts, second secret code is generated for the AI
- unique game id is generated, returned to the player to store in the client (e.g. browser)
- separate process is created for the AI to guess the secret code
- outputs from the AI are stored in a database

- player makes a guess and receives feedback
- client sends request for the AI's next guess
- repeat until either the player or AI wins

### AI vs AI

- a secret code for both AI agents is generated
- two separate processes are created for the AI agents to guess the secret code
- outputs from the AI agents are stored in a database
- game engine streams updates on the game state to the client via SSE

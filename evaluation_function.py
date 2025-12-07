def validate_input(s: str) -> None:
    if len(s) != 4:
        raise ValueError("Input must be a string of length 4")

    if len(set(s)) != 4:
        raise ValueError("Input must contain 4 unique digits")

    if not s.isdigit():
        raise ValueError("Input must contain only digits")


def evaluate_guess(guess: str, secret: str) -> tuple[int, int]:
    """
    Evaluate a guess against a secret code.
    """

    validate_input(guess)
    validate_input(secret)

    correct_positions = 0
    correct_numbers = 0

    for i in range(len(guess)):
        if guess[i] == secret[i]:
            correct_positions += 1
        elif guess[i] in secret:
            correct_numbers += 1

    return correct_positions, correct_numbers

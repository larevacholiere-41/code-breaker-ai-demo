from evaluation_function import evaluate_guess


def test_evaluate_guess():
    assert evaluate_guess("1234", "1234") == (4, 0)
    assert evaluate_guess("1234", "5678") == (0, 0)
    assert evaluate_guess("1234", "1235") == (3, 0)
    assert evaluate_guess("1234", "1243") == (2, 2)
    assert evaluate_guess("1234", "4321") == (0, 4)

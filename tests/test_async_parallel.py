import asyncio
from datetime import datetime
from random import sample
from chains.guesser_v1 import AsyncGuesserV1
from chains.guesser_v3 import AsyncGuesserV3
from tests.agent_test_runner import test_agent_simplified_async

MAX_ATTEMPTS = 20


async def test_parallel_v1_and_v3():
    """Test AsyncGuesserV1 and AsyncGuesserV3 in parallel."""
    # Generate a shared secret code for fair comparison
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"Secret code: {secret_code}")

    # Create tasks for both guessers
    async def test_v1():
        t1 = datetime.now()
        guesser_v1 = AsyncGuesserV1()
        success, attempts = await test_agent_simplified_async(
            guesser_v1, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        duration = (t2 - t1).total_seconds()
        return ("V1", success, attempts, duration)

    async def test_v3():
        t1 = datetime.now()
        guesser_v3 = AsyncGuesserV3()
        success, attempts = await test_agent_simplified_async(
            guesser_v3, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        duration = (t2 - t1).total_seconds()
        return ("V3", success, attempts, duration)

    # Run both tests in parallel
    results = await asyncio.gather(test_v1(), test_v3())

    # Display results
    print("\n" + "=" * 60)
    print("PARALLEL TEST RESULTS")
    print("=" * 60)
    for version, success, attempts, duration in results:
        status = "WON" if success else "LOST"
        print(f"{version}: {status} in {attempts} attempts ({duration:.2f}s)")
    print("=" * 60)

    return results


async def test_parallel_multiple_rounds():
    """Run multiple rounds of parallel tests to compare performance."""
    num_rounds = 5
    v1_wins = 0
    v3_wins = 0
    v1_total_attempts = 0
    v3_total_attempts = 0
    v1_total_time = 0.0
    v3_total_time = 0.0

    print(f"\nRunning {num_rounds} parallel test rounds...")
    print("=" * 60)

    for round_num in range(1, num_rounds + 1):
        print(f"\nRound {round_num}/{num_rounds}")
        results = await test_parallel_v1_and_v3()

        # Process results
        for version, success, attempts, duration in results:
            if version == "V1":
                if success:
                    v1_wins += 1
                v1_total_attempts += attempts
                v1_total_time += duration
            else:  # V3
                if success:
                    v3_wins += 1
                v3_total_attempts += attempts
                v3_total_time += duration

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY AFTER", num_rounds, "ROUNDS")
    print("=" * 60)
    print(f"V1: {v1_wins}/{num_rounds} wins, "
          f"avg {v1_total_attempts/num_rounds:.1f} attempts, "
          f"avg {v1_total_time/num_rounds:.2f}s")
    print(f"V3: {v3_wins}/{num_rounds} wins, "
          f"avg {v3_total_attempts/num_rounds:.1f} attempts, "
          f"avg {v3_total_time/num_rounds:.2f}s")
    print("=" * 60)

    return {
        "v1_wins": v1_wins,
        "v3_wins": v3_wins,
        "v1_avg_attempts": v1_total_attempts / num_rounds,
        "v3_avg_attempts": v3_total_attempts / num_rounds,
        "v1_avg_time": v1_total_time / num_rounds,
        "v3_avg_time": v3_total_time / num_rounds,
    }


if __name__ == "__main__":
    # Run a single parallel test
    asyncio.run(test_parallel_v1_and_v3())

    # Uncomment to run multiple rounds
    # asyncio.run(test_parallel_multiple_rounds())

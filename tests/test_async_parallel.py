import asyncio
from pytest import mark
from datetime import datetime
from random import sample
from chains.guesser_v1 import AsyncGuesserV1
from chains.guesser_v3 import AsyncGuesserV3
from tests.agent_test_runner import test_agent_simplified_async

MAX_ATTEMPTS = 20


@mark.asyncio
async def test_parallel_v1_and_v3():
    """Test AsyncGuesserV1 and AsyncGuesserV3 in parallel."""
    # Generate a shared secret code for fair comparison
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"Secret code: {secret_code}")

    # Create tasks for both guessers
    async def v1():
        t1 = datetime.now()
        guesser_v1 = AsyncGuesserV1()
        success, attempts = await test_agent_simplified_async(
            guesser_v1, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        duration = (t2 - t1).total_seconds()
        return ("V1", success, attempts, duration)

    async def v3():
        t1 = datetime.now()
        guesser_v3 = AsyncGuesserV3()
        success, attempts = await test_agent_simplified_async(
            guesser_v3, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        duration = (t2 - t1).total_seconds()
        return ("V3", success, attempts, duration)

    # Run both tests in parallel
    results = await asyncio.gather(v1(), v3())

    # Display results
    print("\n" + "=" * 60)
    print("PARALLEL TEST RESULTS")
    print("=" * 60)
    for version, success, attempts, duration in results:
        status = "WON" if success else "LOST"
        print(f"{version}: {status} in {attempts} attempts ({duration:.2f}s)")
    print("=" * 60)

    return results

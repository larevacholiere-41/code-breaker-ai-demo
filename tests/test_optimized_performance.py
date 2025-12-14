import asyncio
from datetime import datetime
from random import sample
from chains.guesser_v3 import GuesserV3, AsyncGuesserV3
from chains.guesser_v3_optimized import GuesserV3Optimized, AsyncGuesserV3Optimized
from tests.agent_test_runner import test_agent_simplified, test_agent_simplified_async

MAX_ATTEMPTS = 20


def test_v3_vs_optimized():
    """Compare performance of GuesserV3 vs GuesserV3Optimized."""
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"Secret code: {secret_code}")
    print("=" * 60)

    # Test original V3
    print("Testing GuesserV3...")
    t1 = datetime.now()
    guesser_v3 = GuesserV3()
    success_v3, attempts_v3 = test_agent_simplified(
        guesser_v3, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
    t2 = datetime.now()
    duration_v3 = (t2 - t1).total_seconds()

    # Test optimized V3
    print("\nTesting GuesserV3Optimized...")
    t1 = datetime.now()
    guesser_optimized = GuesserV3Optimized()
    success_opt, attempts_opt = test_agent_simplified(
        guesser_optimized, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
    t2 = datetime.now()
    duration_opt = (t2 - t1).total_seconds()

    # Display results
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"GuesserV3:          {'WON' if success_v3 else 'LOST'} in {attempts_v3} attempts ({duration_v3:.2f}s)")
    print(f"GuesserV3Optimized: {'WON' if success_opt else 'LOST'} in {attempts_opt} attempts ({duration_opt:.2f}s)")

    if duration_v3 > 0:
        speedup = ((duration_v3 - duration_opt) / duration_v3) * 100
        print(f"\nSpeedup: {speedup:.1f}% faster")
    print("=" * 60)

    return {
        "v3": (success_v3, attempts_v3, duration_v3),
        "optimized": (success_opt, attempts_opt, duration_opt),
        "speedup_percent": speedup if duration_v3 > 0 else 0
    }


async def test_async_v3_vs_optimized():
    """Compare performance of AsyncGuesserV3 vs AsyncGuesserV3Optimized."""
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"Secret code: {secret_code}")
    print("=" * 60)

    # Test async V3
    print("Testing AsyncGuesserV3...")
    t1 = datetime.now()
    guesser_v3 = AsyncGuesserV3()
    success_v3, attempts_v3 = await test_agent_simplified_async(
        guesser_v3, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
    t2 = datetime.now()
    duration_v3 = (t2 - t1).total_seconds()

    # Test async optimized V3
    print("\nTesting AsyncGuesserV3Optimized...")
    t1 = datetime.now()
    guesser_optimized = AsyncGuesserV3Optimized()
    success_opt, attempts_opt = await test_agent_simplified_async(
        guesser_optimized, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
    t2 = datetime.now()
    duration_opt = (t2 - t1).total_seconds()

    # Display results
    print("\n" + "=" * 60)
    print("ASYNC PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f"AsyncGuesserV3:          {'WON' if success_v3 else 'LOST'} in {attempts_v3} attempts ({duration_v3:.2f}s)")
    print(f"AsyncGuesserV3Optimized: {'WON' if success_opt else 'LOST'} in {attempts_opt} attempts ({duration_opt:.2f}s)")

    if duration_v3 > 0:
        speedup = ((duration_v3 - duration_opt) / duration_v3) * 100
        print(f"\nSpeedup: {speedup:.1f}% faster")
    print("=" * 60)

    return {
        "v3": (success_v3, attempts_v3, duration_v3),
        "optimized": (success_opt, attempts_opt, duration_opt),
        "speedup_percent": speedup if duration_v3 > 0 else 0
    }


async def test_parallel_comparison():
    """Run both optimized versions in parallel to test concurrency."""
    secret_code = "".join(str(digit) for digit in sample(range(10), 4))
    print(f"\nParallel Execution Test")
    print(f"Secret code: {secret_code}")
    print("=" * 60)

    async def test_opt1():
        t1 = datetime.now()
        guesser = AsyncGuesserV3Optimized()
        success, attempts = await test_agent_simplified_async(
            guesser, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        return ("Instance 1", success, attempts, (t2 - t1).total_seconds())

    async def test_opt2():
        t1 = datetime.now()
        guesser = AsyncGuesserV3Optimized()
        success, attempts = await test_agent_simplified_async(
            guesser, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        return ("Instance 2", success, attempts, (t2 - t1).total_seconds())

    # Run both in parallel
    results = await asyncio.gather(test_opt1(), test_opt2())

    print("\nParallel execution results:")
    for name, success, attempts, duration in results:
        print(f"{name}: {'WON' if success else 'LOST'} in {attempts} attempts ({duration:.2f}s)")
    print("=" * 60)

    return results


async def benchmark_multiple_rounds():
    """Run multiple rounds to get average performance metrics."""
    num_rounds = 10
    v3_total_time = 0.0
    opt_total_time = 0.0
    v3_wins = 0
    opt_wins = 0

    print(f"\nRunning {num_rounds} benchmark rounds...")
    print("=" * 60)

    for round_num in range(1, num_rounds + 1):
        secret_code = "".join(str(digit) for digit in sample(range(10), 4))
        print(f"Round {round_num}/{num_rounds} (code: {secret_code})")

        # Test V3
        t1 = datetime.now()
        guesser_v3 = AsyncGuesserV3()
        success_v3, _ = await test_agent_simplified_async(
            guesser_v3, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        v3_time = (t2 - t1).total_seconds()
        v3_total_time += v3_time
        if success_v3:
            v3_wins += 1

        # Test Optimized
        t1 = datetime.now()
        guesser_opt = AsyncGuesserV3Optimized()
        success_opt, _ = await test_agent_simplified_async(
            guesser_opt, secret_code=secret_code, max_attempts=MAX_ATTEMPTS)
        t2 = datetime.now()
        opt_time = (t2 - t1).total_seconds()
        opt_total_time += opt_time
        if success_opt:
            opt_wins += 1

        print(f"  V3: {v3_time:.2f}s, Optimized: {opt_time:.2f}s")

    avg_v3_time = v3_total_time / num_rounds
    avg_opt_time = opt_total_time / num_rounds
    speedup = ((avg_v3_time - avg_opt_time) / avg_v3_time) * 100

    print("\n" + "=" * 60)
    print(f"BENCHMARK RESULTS ({num_rounds} rounds)")
    print("=" * 60)
    print(f"AsyncGuesserV3:          {v3_wins}/{num_rounds} wins, avg {avg_v3_time:.2f}s")
    print(f"AsyncGuesserV3Optimized: {opt_wins}/{num_rounds} wins, avg {avg_opt_time:.2f}s")
    print(f"\nAverage Speedup: {speedup:.1f}% faster")
    print("=" * 60)

    return {
        "avg_v3_time": avg_v3_time,
        "avg_opt_time": avg_opt_time,
        "speedup_percent": speedup,
        "v3_wins": v3_wins,
        "opt_wins": opt_wins,
    }


if __name__ == "__main__":
    # Synchronous comparison
    print("\n1. SYNCHRONOUS COMPARISON")
    test_v3_vs_optimized()

    # Async comparison
    print("\n\n2. ASYNC COMPARISON")
    asyncio.run(test_async_v3_vs_optimized())

    # Parallel test
    print("\n\n3. PARALLEL EXECUTION TEST")
    asyncio.run(test_parallel_comparison())

    # Benchmark (uncomment for thorough testing)
    # print("\n\n4. BENCHMARK")
    # asyncio.run(benchmark_multiple_rounds())

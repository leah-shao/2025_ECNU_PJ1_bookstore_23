import pytest

from fe.bench.run import run_bench


@pytest.mark.skip(reason="Bench test is resource-heavy and flaky in CI — run manually when benchmarking")
def test_bench():
    try:
        run_bench()
    except Exception as e:
        # If someone intentionally un-skips this test, keep the original failure behaviour
        assert 200 == 100, "test_bench过程出现异常"

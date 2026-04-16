import pytest
from scraper.ratelimiter import WindowRateLimiter,DelayRateLimiter
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_delay_limiter_triggers_sleep(mocker):
    # 1. Mock asyncio.sleep so the test doesn't actually hang
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    
    # 2. Setup Limiter with a 5-second delay
    limiter = DelayRateLimiter(delay=5)
    
    # First call happens at T=0
    await limiter.is_allowed()
    
    # Second call happens immediately (T=0.1)
    # The limiter should calculate a ~4.9s wait
    await limiter.is_allowed()
    
    # 3. Assertions
    mock_sleep.assert_called_once()
    # Check if it tried to sleep for roughly 5 seconds
    args, _ = mock_sleep.call_args
    assert 4.0 <= args[0] <= 5.0

@pytest.mark.asyncio
@pytest.mark.freeze_time("2026-04-16 12:00:00")
async def test_delay_limiter_no_trigger_sleep(mocker,freezer):
    # 1. Mock asyncio.sleep so the test doesn't actually hang
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    
    # 2. Setup Limiter with a 5-second delay
    limiter = DelayRateLimiter(delay=5)
    await limiter.is_allowed()

    # Teleport 5 minute into the future
    freezer.move_to("2026-04-16 12:05:01")
    
    await limiter.is_allowed()
    
    # 3. Assertions
    mock_sleep.assert_not_called()





@pytest.mark.asyncio
async def test_window_limiter_triggers_sleep(mocker):
    # 1. Mock asyncio.sleep so the test doesn't actually hang
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    
    # 2. Setup Limiter with a 5-second delay
    limiter = WindowRateLimiter(rate=1)
    
    # First call happens at T=0
    await limiter.is_allowed()
    
    # Second call happens immediately (T=0.1)
    await limiter.is_allowed()
    
    # 3. Assertions
    mock_sleep.assert_called_once()
    # Check if it tried to sleep for roughly 5 seconds
    args, _ = mock_sleep.call_args
    assert 0.0 <= args[0] <= 60.0

@pytest.mark.asyncio
@pytest.mark.freeze_time("2026-04-16 12:00:00")
async def test_window_limiter_no_trigger_sleep(mocker,freezer):
    # 1. Mock asyncio.sleep so the test doesn't actually hang
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    
    # 2. Setup Limiter with a 5-second delay
    limiter = WindowRateLimiter(rate=1)
    await limiter.is_allowed()

    # Teleport 1 minute into the future
    freezer.move_to("2026-04-16 12:01:01")
    
    await limiter.is_allowed()
    
    # 3. Assertions
    mock_sleep.assert_not_called()

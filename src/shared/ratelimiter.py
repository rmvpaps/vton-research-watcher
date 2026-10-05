import asyncio
from datetime import datetime,timezone,timedelta
import logging
from abc import ABC, abstractmethod

class RateLimiter(ABC):
    @abstractmethod
    async def is_allowed(self):
        """
        Immediately returns if allowed. Else sleeps till next allowed time
        """
        pass


class WindowRateLimiter:
    """
    Set Rate per minute. Delay till next window if exceeded
    """
    def __init__(self, rate: int):
        self.rate = rate
        self.count = 0
        self.next_slab_ts = datetime.now(timezone.utc) + timedelta(minutes=1)
        self._lock = asyncio.Lock()  # Prevents race conditions

    async def is_allowed(self):
        async with self._lock:  # Ensure only one task updates the counter at a time
            cur_ts = datetime.now(timezone.utc)
            
            # If the current window has expired
            if cur_ts >= self.next_slab_ts:
                logging.info("Ratelimter: Resetting window")
                # Reset window to the next full minute slab
                self.next_slab_ts = cur_ts + timedelta(minutes=1)
                self.count = 0

            # If we are over the limit within the current window
            if self.count >= self.rate:
                diff = (self.next_slab_ts - cur_ts).total_seconds()
                if diff > 0:
                    logging.info(f"Ratelimter: Limit reached. Sleeping for {diff:.2f}s")
                    await asyncio.sleep(diff)  
                    
                    # After waking up, we are in a fresh window
                    self.next_slab_ts = datetime.now(timezone.utc) + timedelta(minutes=1)
                    self.count = 1
                    return True

            # Within limits
            self.count += 1
            logging.debug(f"Ratelimter: Allowed ({self.count}/{self.rate})")
            return True    

        


class DelayRateLimiter:
    def __init__(self, delay: int):
        self.delay_delta = timedelta(seconds=delay)
        # Initialize in the past so the first call is instant
        self.last_ts = datetime.now(timezone.utc) - self.delay_delta
        self._lock = asyncio.Lock()

    async def is_allowed(self):
        async with self._lock:
            cur_ts = datetime.now(timezone.utc)
            diff = cur_ts - self.last_ts
            
            if diff < self.delay_delta:
                wait_time = (self.last_ts + self.delay_delta - cur_ts).total_seconds()
                logging.info(f"Ratelimter: Throttling for {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
                # Update to the time it WAS ALLOWED to run, not when it woke up
                # This keeps the cadence consistent
                self.last_ts = self.last_ts + self.delay_delta
            else:
                # No wait needed, reset reference to now
                self.last_ts = cur_ts
            
            return True
        


class RateLimiterFactory:
    _ratelimiters = {
        "window": WindowRateLimiter,
        "delay": DelayRateLimiter
    }

    @classmethod
    def get_rate_limiter(cls, ratelimiter_type: str, **kwargs) -> RateLimiter:
        ratelimiter_class = cls._ratelimiters.get(ratelimiter_type.lower())
        if not ratelimiter_class:
            raise ValueError(f"Unknown rate limiter type: {ratelimiter_type}")
        return ratelimiter_class(**kwargs)


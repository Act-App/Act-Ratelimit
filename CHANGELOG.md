# Act_Ratelimit 1.0.0 (2025-02-02)

### Features

- Added `ACTRatelimit.disabled` which can be used to completely disable the rate limiting for all routes. This may be used for developing purposes
- Support for multiple "Backends" using `act_ratelimit.backends`. This allows for usage of `redis`, `valkey` or any other key value storage.
- Support for multiple ratelimit strategies using `RateLimitStrategy`.

### Bugfixes

- Added checks to prevent users to enter invalid arguments to `RateLimiter`
- Fixed AttributeError when using rate-limiting for a route that has a similar websocket route.

### Miscellaneous

- Redis call to `.close()` was deprecated in 5.0.1, switched to `.aclose()`


# Act_Ratelimit 0.0.1a2 (2025-02-02)

### Miscellaneous

- first prerelease to test deploying

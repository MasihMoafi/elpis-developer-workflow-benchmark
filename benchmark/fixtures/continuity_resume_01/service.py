def remaining_retries(attempts, limit):
    """Return the number of retries still available after attempts."""
    return max(0, limit + attempts)

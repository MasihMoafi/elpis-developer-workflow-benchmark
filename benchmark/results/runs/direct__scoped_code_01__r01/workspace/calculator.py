def apply_discount(cents, percentage):
    """Return the price after a percentage discount, in whole cents."""
    return int(cents * (100 - percentage) / 100)

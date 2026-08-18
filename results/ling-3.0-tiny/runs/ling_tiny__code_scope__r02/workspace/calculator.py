def apply_discount(cents: int, percentage: int) -> int:
    if percentage < 0 or percentage > 100:
        raise ValueError("percentage must be between 0 and 100")
    return cents * (100 + percentage) // 100


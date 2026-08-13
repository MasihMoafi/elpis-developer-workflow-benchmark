for index in range(2400):
    print(f"DEBUG request={index:04d} cache=miss payload={'x' * 42}")
    if index % 37 == 0:
        print(f"DRAFT rollout_mode=canary source=proposal-{index}")
    if index == 1217:
        print("AUTHORITATIVE rollout_mode=stable source=release-board")

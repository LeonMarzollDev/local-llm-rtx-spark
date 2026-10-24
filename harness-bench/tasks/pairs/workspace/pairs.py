def unique_pairs(nums, target):
    """All different pairs (a, b) with a <= b, a + b == target, a and b taken from nums
    (a and b may be the same number only if it occurs at least twice). Sorted ascending."""
    result = []
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] + nums[j] == target:
                pair = (min(nums[i], nums[j]), max(nums[i], nums[j]))
                if pair not in result:
                    result.append(pair)
    return sorted(result)

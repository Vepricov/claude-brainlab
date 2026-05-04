> GitHub: https://github.com/quan16369/Kaggle-Konwinski-Prize-6th-Place-Solution-

---

|------|------------|-----------|
| Select-Patch-Verify-Choose | 0.008237 (3 correct, 2 wrong, 115 skipped) | -0.000097 (1 correct, 1 wrong, 69 skipped) |

---

```
┌─────────────┐
└──────┬──────┘
       │
       ▼
┌─────────────┐
└──────┬──────┘
       │
       ▼
┌─────────────┐
└──────┬──────┘
       │
       ▼
┌─────────────┐
└─────────────┘
```

---

```python
[
]
```

---

```python
def calculate_patch_score(patch, judgments):
    if not is_valid(patch) or judgments.count(True) == 0:
        return -LARGE_PENALTY

    score = (judgments.count(True) ** 2) * 5.0

    score -= (np.exp(len(patch) / 10) - 1)

    return score
```

---

```
penalty = exp(patch_length / 10) - 1
```

---

```python
def choose_patch_string_optimized(
    patches: List[str],
    judgments_aggregated: List[List[bool]],
    dry_run_results: List[bool],
    top_percentile: float = 0.01,
    min_yes_votes: int = 3,
    large_penalty: float = 1e6
) -> Optional[int]:
    """

    Args:

    Returns:
    """
    scores = []
    for i, (patch, judgments, dry_run_ok) in enumerate(
        zip(patches, judgments_aggregated, dry_run_results)
    ):
        if not dry_run_ok or not judgments:
            scores.append(-large_penalty)
            continue

        yes_votes = sum(judgments)
        if yes_votes == 0:
            scores.append(-large_penalty)
            continue

        score = (yes_votes ** 2) * 5.0

        score -= np.exp(len(patch) / 10) - 1

        scores.append(score)

    max_score = max(scores)
    if max_score <= 0:

    threshold = np.percentile(scores, 100 * (1 - top_percentile))
    if max_score < threshold:
        return None

    best_idx = scores.index(max_score)

    sorted_scores = sorted(scores, reverse=True)
    if len(sorted_scores) > 1 and max_score < sorted_scores[1] * 1.5:
        return None

    if sum(judgments_aggregated[best_idx]) < min_yes_votes:
        return None

    return best_idx
```

---

---

---

```python
def multi_attempt_verify(
    patch: str,
    context: str,
    num_attempts: int = 3,
    model: str = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
) -> List[bool]:
    """

    Returns:
    """
    judgments = []

    for _ in range(num_attempts):
        response = llm_call(
            model=model,
            messages=[{
                "role": "user",

{context}

{patch}

            }]
        )

        judgment = "yes" in response.lower()
        judgments.append(judgment)

    return judgments
```

```python
def score_patch(
    patch: str,
    yes_votes: int,
    base_weight: float = 5.0,
    size_penalty_scale: float = 10.0
) -> float:
    """

    Args:

    Returns:
    """
    score = (yes_votes ** 2) * base_weight

    size_penalty = np.exp(len(patch) / size_penalty_scale) - 1
    score -= size_penalty

    return score
```

```python
async def spvc_pipeline(
    bug_report: str,
    code_tree: Dict[str, str],
    model: str = "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
) -> Optional[str]:
    """

    Returns:
    """
    # 1. Select
    selections = await select_phase(bug_report, code_tree, model)

    # 2. Patch
    patches = await patch_phase(selections, model)

    # 3. Verify
    judgments_aggregated = []
    for patch in patches:
        judgments = multi_attempt_verify(patch, bug_report, model=model)
        judgments_aggregated.append(judgments)

    # 4. Choose
    best_idx = choose_patch_string_optimized(
        patches=patches,
        judgments_aggregated=judgments_aggregated,
    )

    return patches[best_idx] if best_idx is not None else None
```

---

- **6th Place Solution**: https://github.com/quan16369/Kaggle-Konwinski-Prize-6th-Place-Solution-

- **Strategy Guide**: https://github.com/raymyers/konwinski-prize-strategy-guide

- **SWE-bench**: https://www.swebench.com/

---

# QALIS Red Team — Evaluation Prompts

Auto-scorer prompts and human review materials for red-team evaluation.

## Files

| File | Description |
|------|-------------|
| `success_judge_prompt.txt` | GPT-4o auto-scorer prompt template |
| `category_rubrics.json` | Per-category success criteria and edge cases |
| `human_review_checklist.md` | Reviewer guide (10% random sample) |

## Evaluation Protocol

1. **Auto-scorer** (`success_judge_prompt.txt`): GPT-4o-2024-08-06 judges each
   attempt as SUCCESS or BLOCKED based on the system's response.
2. **Human review** (`human_review_checklist.md`): A random 10% sample is
   manually reviewed per `configs/red_team_config.yaml > evaluation.human_review_fraction`.
3. **Category rubrics** (`category_rubrics.json`): Per-category success criteria
   are injected into `{success_criteria}` in the auto-scorer prompt.

## Auto-scorer Accuracy

Inter-rater agreement between auto-scorer and human reviewers: **κ = 0.89**
(Cohen's κ, 10% sample, n ≈ 285 attempts).

## Configuration

`configs/red_team_config.yaml > evaluation`

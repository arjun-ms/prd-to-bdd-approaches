# Approach 3: Cosine Similarity with 90% Threshold

## Overview

This approach uses **cosine similarity** with a **0.9 (90%) threshold** to detect and remove duplicate BDD scenarios. It is the **most conservative** approach, only removing scenarios that are extremely similar while preserving nuanced variations.

## Methodology

### 1. **Semantic Embedding**
- Uses the `intfloat/e5-large-v2` sentence transformer model
- Converts each BDD scenario (Given + When + Then) into a dense vector embedding
- Captures semantic meaning for accurate similarity comparison

### 2. **Similarity Calculation**
- Computes cosine similarity between all scenario pairs
- Similarity scores range from 0 (completely different) to 1 (identical)
- **High threshold (0.9)** means only near-identical scenarios are flagged

### 3. **Contrast Pair Detection**
- Extended list of contradictory keyword pairs
- Prevents marking scenarios as duplicates when they describe opposite outcomes
- Checks for contradictory keywords in `When` and `Then` clauses:
  - success ↔ error
  - approve ↔ reject
  - completed ↔ failed
  - allow ↔ deny
  - valid ↔ invalid
  - accepted ↔ rejected
  - active ↔ inactive
  - authenticated ↔ unauthorized

### 4. **Deduplication Logic**
```python
if similarity > 0.9 AND no_contrast_detected:
    mark_as_duplicate()
```

## Advantages

✅ **Highest Precision**: Minimal false positives  
✅ **Preserves Nuance**: Keeps subtly different scenarios  
✅ **Safe for Production**: Low risk of removing important variations  
✅ **Fast Processing**: No additional LLM calls required  
✅ **Deterministic**: Same input always produces same output  
✅ **Cost-Effective**: Uses local embeddings, no API costs  
✅ **Extended Contrast Pairs**: Better detection of opposite scenarios  

## Disadvantages

❌ **Lower Recall**: May miss genuinely duplicate scenarios  
❌ **Manual Review Still Needed**: Some duplicates may remain  
❌ **Paraphrase-Sensitive**: Different wording may not be caught  
❌ **Not Aggressive Enough**: For very redundant PRDs, may need multiple passes  




## When to Use This Approach

### ✅ Best For:
- Well-written PRDs with minimal redundancy
- Production environments requiring high precision
- When false positives are costly
- Quality-critical projects
- Initial deduplication pass (can follow with manual review)
- Conservative organizations

### ❌ Avoid When:
- PRD has extreme redundancy
- Quick aggressive cleanup needed
- You want to maximize duplicate removal
- Manual review is difficult/impossible




## Output Files

| File | Description |
|------|-------------|
| `bdd_output_raw_approach3.json` | Original scenarios before deduplication |
| `bdd_output_deduped_approach3.json` | Cleaned scenarios after deduplication |
| `duplicates_report_90.csv` | Detailed report of all removed duplicates |





## Configuration

```python
# Adjustable parameters
threshold = 0.9  # Similarity threshold (90%)
model = 'intfloat/e5-large-v2'  # Embedding model

# Extended contrast pairs (more comprehensive than Approach 1)
contrast_pairs = [
    ("success", "error"),
    ("approve", "reject"),
    ("valid", "invalid"),
    ("authenticated", "unauthorized"),
    # ... more pairs
]
```





## Comparison with Other Approaches

| Metric | Approach 3 (90%) | Approach 1 (80%) | Approach 2 (NLI) |
|--------|------------------|------------------|------------------|
| Precision | Highest | Good | Very High |
| Recall | Lower | Higher | Highest |
| Speed | Fast | Fast | Slow |
| False Positives | Minimal | Some | Very Low |
| False Negatives | More | Fewer | Minimal |
| Best Use Case | Production | Prototyping | Research |




### Visual Comparison

```
Approach 1 (80%): ████████████████░░░░ (More aggressive)
Approach 3 (90%): ████████░░░░░░░░░░░░ (More conservative)
Approach 2 (NLI): ██████████████████░░ (Most accurate)
```




## Threshold Selection Guide

| Threshold | Behavior | Use Case |
|-----------|----------|----------|
| 0.95+ | Only exact/near-exact matches | Ultra-conservative, final QA |
| 0.90-0.94 | Very similar scenarios | **Recommended for production** |
| 0.85-0.89 | Similar scenarios | Balanced approach |
| 0.80-0.84 | Somewhat similar | Aggressive cleanup |
| <0.80 | Many false positives | Not recommended |






## Example Output

```
🧹 Before cleanup: 847 scenarios
❌🗑️ Removed 68 DUPLICATE SCENARIOS.
✅ After cleanup: 779 scenarios

🔍 Duplicate scenario pairs (showing top 10 by similarity):

🧩 Similarity: 0.968
🅰️ Scenario A: Given user is logged in When they click logout Then they are redirected to home
🅱️ Scenario B: Given user is logged in When they click logout button Then they are redirected to homepage

🧩 Similarity: 0.947
🅰️ Scenario A: Given valid credentials When user attempts login Then authentication succeeds
🅱️ Scenario B: Given valid credentials When user tries to log in Then authentication is successful
```







## Troubleshooting

### Problem: Still finding manual duplicates after cleanup
**Solution**: Lower threshold to 0.85 or 0.88

### Problem: Important test variations were removed
**Solution**: 
- Increase threshold to 0.92 or 0.95
- Add specific contrast pairs for your domain
- Review and restore from raw JSON

### Problem: Too few duplicates removed
**Solution**: This might be correct! Check if:
- Your PRD is well-written with minimal redundancy
- LLM generated diverse scenarios
- You need a more aggressive approach (try Approach 1)

### Problem: Contrast pairs not catching opposites
**Solution**: Add domain-specific pairs:
```python
contrast_pairs.extend([
    ("buyer", "seller"),      # marketplace domain
    ("deposit", "withdrawal"), # finance domain
    ("upload", "download"),    # file management
])
```




## When to Upgrade to Approach 2 (NLI)

Consider upgrading if:
- You need to detect contradictions, not just duplicates
- False negatives are costly (missed duplicates cause issues)
- You have GPU resources available
- Accuracy is more important than speed
- You're working on critical/regulated systems

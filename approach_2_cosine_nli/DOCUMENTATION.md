# Approach 2: Cosine Similarity + Natural Language Inference (NLI)

## Overview

This approach combines **cosine similarity** with **Natural Language Inference (NLI)** to provide the most sophisticated duplicate detection and relationship analysis. It not only identifies similar scenarios but also classifies the semantic relationship between them (entailment, contradiction, or neutral).



## Methodology

### 1. **Semantic Embedding**
- Uses `all-mpnet-base-v2` sentence transformer model
- Generates dense vector embeddings for each Given/When/Then step
- Compares individual clauses rather than full scenarios

### 2. **Cosine Similarity Filtering**
- Initial similarity threshold: **0.6** (60%)
- Reduces computational load by skipping NLI for clearly different scenarios
- Full similarity analysis using cosine distance

### 3. **Natural Language Inference (NLI)**
- Uses `roberta-large-mnli` model (trained on Multi-Genre NLI dataset)
- Classifies relationship between sentence pairs:
  - **ENTAILMENT**: One sentence logically follows from another
  - **CONTRADICTION**: Sentences express opposite/conflicting information
  - **NEUTRAL**: No clear logical relationship

### 4. **Decision Logic**
```python
if similarity > 0.8:
    if NLI == ENTAILMENT:
        → "Likely Duplicate"
    elif NLI == CONTRADICTION:
        → "Contradictory"
    else:
        → "Similar but Unclear"
else:
    → "Not Similar"
```

## Advantages

✅ **Highest Accuracy**: Understands semantic relationships beyond keyword matching  
✅ **Detects Contradictions**: Identifies conflicting requirements automatically  
✅ **Handles Paraphrasing**: Recognizes entailment even with different wording  
✅ **Detailed Analysis**: Provides confidence scores and relationship labels  
✅ **Granular Insights**: Analyzes individual Given/When/Then steps  
✅ **Research-Grade**: Based on state-of-the-art NLP models  

## Disadvantages

❌ **Computationally Expensive**: Much slower than pure cosine similarity  
❌ **High Memory Usage**: Requires GPU for reasonable speed  
❌ **Complex Setup**: Needs transformers library and large models  
❌ **Not Automatic**: Provides analysis but requires manual review  
❌ **Longer Processing**: Can take 10-30 minutes for large PRDs  

## When to Use This Approach

### ✅ Best For:
- Critical projects where accuracy is paramount
- Detecting subtle contradictions in requirements
- Complex PRDs with nuanced language
- Research and analysis purposes
- When you have GPU resources available

### ❌ Avoid When:
- Quick turnaround needed
- Limited computational resources
- Simple, straightforward PRDs
- Fully automated pipeline required
- Budget constraints (cloud GPU costs)

## Output Files

| File | Description |
|------|-------------|
| `bdd_output_raw_approach2.json` | Original scenarios before analysis |
| `nli_comparison_results.csv` | Detailed pair-wise analysis with NLI labels |



## Key Metrics in Output

The CSV file contains:

| Column | Description |
|--------|-------------|
| Step 1 | First BDD step in comparison |
| Step 2 | Second BDD step in comparison |
| Similarity | Cosine similarity score (0-1) |
| NLI Label | ENTAILMENT / CONTRADICTION / NEUTRAL |
| Confidence | NLI model confidence (0-100%) |
| Decision | Final classification of relationship |



## Configuration

```python
# Model configuration
embedder = SentenceTransformer('all-mpnet-base-v2')
nli_model = pipeline("text-classification", model="roberta-large-mnli")

# Thresholds
similarity_threshold_for_nli = 0.6  # Skip NLI below this
duplicate_threshold = 0.8  # Mark as duplicate above this

# Device
device = 'cuda' if torch.cuda.is_available() else 'cpu'
```




## Understanding NLI Labels

### ENTAILMENT
**Meaning**: Scenario B is a logical consequence of Scenario A

**Example**:
- **A**: "Given user has admin privileges When they access settings Then they see advanced options"
- **B**: "Given administrator When accessing configuration Then advanced settings visible"
- **Interpretation**: These are likely duplicates (same requirement, different wording)

### CONTRADICTION
**Meaning**: Scenarios express mutually exclusive or opposite outcomes

**Example**:
- **A**: "When user clicks submit Then form is accepted"
- **B**: "When user clicks submit Then form is rejected"
- **Interpretation**: These are conflicting requirements (needs resolution)

### NEUTRAL
**Meaning**: No clear logical relationship

**Example**:
- **A**: "When user logs in Then dashboard loads"
- **B**: "When user clicks profile Then settings appear"
- **Interpretation**: Different scenarios describing different functionality





## Usage

```python
# Run full NLI analysis
df_results, bdd_steps = analyze_bdd_steps_with_nli(bdd_json['features'])

# Filter for duplicates
duplicates = df_results[df_results['Decision'] == '✅ Likely Duplicate']

# Filter for contradictions
contradictions = df_results[df_results['Decision'] == '❌ Contradictory']

# Review high-confidence duplicates
high_conf_dups = duplicates[duplicates['Confidence'] > 90]
```






## Comparison with Other Approaches

| Metric | Approach 2 (NLI) | Approach 1 (80%) | Approach 3 (90%) |
|--------|------------------|------------------|------------------|
| Accuracy | Highest | Good | Better |
| Speed | Slowest | Fast | Fast |
| Contradiction Detection | Yes | No | No |
| GPU Required | Recommended | No | No |
| Automation | Manual Review | Automatic | Automatic |
| Cost (Cloud) | High | Low | Low |






## Interpreting Results

### High Similarity + Entailment
→ **Strong duplicate candidate** - review and likely remove one

### High Similarity + Contradiction
→ **Requirement conflict** - requires stakeholder clarification

### High Similarity + Neutral
→ **Similar but distinct** - probably keep both, may need better differentiation

### Low Similarity (any NLI label)
→ **Different scenarios** - keep both





## Advanced Usage

### Filter by Confidence
```python
# Only high-confidence predictions
reliable = df_results[df_results['Confidence'] > 85]

# Uncertain cases for manual review
uncertain = df_results[
    (df_results['Similarity'] > 0.7) & 
    (df_results['Confidence'] < 70)
]
```

### Identify Contradiction Clusters
```python
contradictions = df_results[df_results['NLI Label'] == 'CONTRADICTION']
contradiction_report = contradictions.sort_values('Similarity', ascending=False)
```





## Example Output

```
✅ Extracted 2541 total BDD steps for comparison.

Using device: cuda

Total pairs to compare: 3227370
Encoding all steps once for efficiency...
✅ Embeddings ready.

Comparing pairs: 100%|██████████| 3227370/3227370 [15:23<00:00, 3492.47it/s]

--- Summary of BDD Step Analysis ---
Total individual steps analyzed: 2541
Pairs identified as Likely Duplicates: 187
Pairs identified as Contradictory: 23
Number of scenarios before cleanup: 847
------------------------------------

✅ Detailed analysis saved to 'nli_comparison_results.csv'
```




## Sample CSV Output

```csv
Step 1,Step 2,Similarity,NLI Label,Confidence,Decision
"When: user logs in","When: user authenticates",0.9234,ENTAILMENT,94.32,"✅ Likely Duplicate"
"Then: payment succeeds","Then: payment fails",0.8521,CONTRADICTION,91.45,"❌ Contradictory"
"Given: user has account","Given: user is registered",0.8756,ENTAILMENT,89.67,"✅ Likely Duplicate"
```

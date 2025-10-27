# PRD to BDD Converter - Multiple Approaches

This project provides **four different approaches** to convert Product Requirements Documents (PRDs) into BDD (Behavior Driven Development) scenarios with intelligent duplicate detection and removal.

## 📁 Project Structure

```
prd_to_bdd_approaches/
├── approach_1_cosine_80/
│   ├── prd_to_bdd_cosine_80.py
│   └── DOCUMENTATION.md
├── approach_2_cosine_nli/
│   ├── prd_to_bdd_cosine_nli.py
│   └── DOCUMENTATION.md
├── approach_3_cosine_90/
│   ├── prd_to_bdd_cosine_90.py
│   └── DOCUMENTATION.md
├── approach_4_llm_checking/
│   ├── prd_to_bdd_llm.py
│   └── DOCUMENTATION.md
└── README.md (this file)
```

## 🎯 Quick Comparison

| Approach | Method | Threshold | Speed | Cost | Accuracy | Best For |
|----------|--------|-----------|-------|------|----------|----------|
| **Approach 1** | Cosine Similarity | 80% | ⚡ Fast | 💰 Low | ⭐⭐⭐ | Prototyping |
| **Approach 2** | Cosine + NLI | 80% + NLI | 🐌 Slow | 💰💰 Medium | ⭐⭐⭐⭐⭐ | Research |
| **Approach 3** | Cosine Similarity | 90% | ⚡ Fast | 💰 Low | ⭐⭐⭐⭐ | Production |
| **Approach 4** | LLM-Based | N/A | 🐢 Slower | 💰💰💰 High | ⭐⭐⭐⭐⭐ | Critical Projects |


<img width="1297" height="390" alt="image" src="https://github.com/user-attachments/assets/340a2e15-28c7-4525-b3b0-c47055324e13" />

## 📊 Detailed Approach Overview

### Approach 1: Cosine Similarity (80% Threshold)
**File**: `approach_1_cosine_80/prd_to_bdd_cosine_80.py`

- **Method**: Semantic embeddings with 80% similarity threshold
- **Contrast Pairs**: Basic set (success/error, approve/reject, etc.)
- **Removal Rate**: 15-25% of scenarios
- **Processing Time**: 2-3 minutes per 1000 scenarios
- **False Positive Rate**: ~5-10%

**Use When**:
- Quick cleanup needed
- High redundancy expected
- Budget is limited
- Prototyping phase

**Avoid When**:
- Nuanced requirements critical
- False positives unacceptable

---

### Approach 2: Cosine Similarity + NLI
**File**: `approach_2_cosine_nli/prd_to_bdd_cosine_nli.py`

- **Method**: Semantic embeddings + Natural Language Inference
- **Models**: all-mpnet-base-v2 + roberta-large-mnli
- **Analysis Type**: Pair-wise comparison with relationship classification
- **Processing Time**: 15-30 minutes per 1000 scenarios (CPU), 5-10 minutes (GPU)
- **Output**: Detailed CSV with NLI labels and confidence scores

**Use When**:
- Need to detect contradictions
- Highest accuracy required
- GPU resources available
- Research or analysis purposes

**Avoid When**:
- Quick results needed
- No GPU available
- Budget constraints

---

### Approach 3: Cosine Similarity (90% Threshold)
**File**: `approach_3_cosine_90/prd_to_bdd_cosine_90.py`

- **Method**: Semantic embeddings with 90% similarity threshold
- **Contrast Pairs**: Extended set (14 pairs)
- **Removal Rate**: 5-10% of scenarios
- **Processing Time**: 2-3 minutes per 1000 scenarios
- **False Positive Rate**: <2%

**Use When**:
- Production deployment
- Well-written PRDs
- High precision critical
- Conservative cleanup preferred

**Avoid When**:
- Extreme redundancy exists
- Aggressive cleanup needed

---

### Approach 4: LLM-Based Checking
**File**: `approach_4_llm_checking/prd_to_bdd_llm.py`

- **Method**: Large Language Model semantic analysis
- **Model**: Gemini 2.0 Flash Exp
- **Batch Processing**: Configurable (default 50 scenarios)
- **Processing Time**: 10-20 minutes per 1000 scenarios
- **API Cost**: ~$0.50-$2.00 per 1000 scenarios

**Use When**:
- Highest accuracy needed
- Budget available for API calls
- Explanation of decisions required
- Complex, nuanced requirements

**Avoid When**:
- Tight budget constraints
- Very large PRDs (>2000 scenarios)
- Offline processing required


---

## 📈 Performance Comparison (1000 Scenarios)

| Metric | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|--------|------------|------------|------------|------------|
| **Time** | 2-3 min | 15-30 min | 2-3 min | 10-20 min |
| **Memory** | 1.5 GB | 4-6 GB | 1.5 GB | 1 GB |
| **GPU Required** | No | Recommended | No | No |
| **API Calls** | 0 | 0 | 0 | ~20 |
| **Cost** | $0 | $0 | $0 | $0.50-$2.00 |
| **Removal Rate** | 15-25% | Analysis only | 5-10% | 10-20% |
| **Accuracy** | Good | Excellent | Very Good | Excellent |


---


## 📝 Output Files

Each approach generates standard output files:

| File | Description |
|------|-------------|
| `bdd_output_raw_approachN.json` | Original scenarios before deduplication |
| `bdd_output_deduped_approachN.json` | Cleaned scenarios after deduplication |
| `duplicates_report_XX.csv` | Detailed duplicate pairs report (Approaches 1, 3) |
| `nli_comparison_results.csv` | NLI analysis results (Approach 2) |

---


## 📚 Documentation

Each approach has detailed documentation in its respective folder:

- **Approach 1**: [DOCUMENTATION.md](approach_1_cosine_80/DOCUMENTATION.md)
- **Approach 2**: [DOCUMENTATION.md](approach_2_cosine_nli/DOCUMENTATION.md)
- **Approach 3**: [DOCUMENTATION.md](approach_3_cosine_90/DOCUMENTATION.md)
- **Approach 4**: [DOCUMENTATION.md](approach_4_llm_checking/DOCUMENTATION.md)

---



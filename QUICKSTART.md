# 🚀 Quick Start Guide - PRD to BDD Converter

Get started in 5 minutes! This guide will help you run your first PRD to BDD conversion.

## ⚡ Super Quick Start (For Approach 3 - Recommended)

```bash
# 1. Install dependencies
pip install sentence-transformers scikit-learn google-genai python-docx PyPDF2

# 2. Set API key
export GEMINI_API_KEY=your-api-key-here  # Linux/Mac
set GEMINI_API_KEY=your-api-key-here     # Windows

# 3. Navigate to approach 3
cd approach_3_cosine_90

# 4. Edit the file and change the PRD path
# Open prd_to_bdd_cosine_90.py and modify:
# file_path = "your_prd_file.pdf"  # Change this line

# 5. Run it!
python prd_to_bdd_cosine_90.py
```

**That's it!** Check the generated JSON files in the directory.



## 📋 Prerequisites

- Python 3.8 or higher
- A Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Your PRD file (PDF or DOCX format)



## 🎯 Step-by-Step for Each Approach

### Approach 1: Cosine Similarity 80% (Aggressive Cleanup)

**When to use**: Quick prototyping, high redundancy expected

```bash
# 1. Install
pip install sentence-transformers scikit-learn google-genai python-docx PyPDF2 pandas

# 2. Set API key
export GEMINI_API_KEY=your-key

# 3. Run
cd approach_1_cosine_80
python prd_to_bdd_cosine_80.py
```

**Expected output**:
- `bdd_output_raw_approach1.json` - Original scenarios
- `bdd_output_deduped_approach1.json` - Cleaned (15-25% removed)
- `duplicates_report_80.csv` - Duplicate details


---

### Approach 2: Cosine + NLI (Analysis & Research)

**When to use**: Need contradiction detection, research purposes

```bash
# 1. Install (includes PyTorch)
pip install sentence-transformers scikit-learn transformers torch tqdm google-genai python-docx PyPDF2 pandas

# 2. Set API key
export GEMINI_API_KEY=your-key

# 3. Run
cd approach_2_cosine_nli
python prd_to_bdd_cosine_nli.py
```

**Expected output**:
- `bdd_output_raw_approach2.json` - Original scenarios
- `nli_comparison_results.csv` - Detailed analysis with NLI labels


**Note**: This approach analyzes but doesn't auto-remove duplicates. Review the CSV to decide what to remove.

---

### Approach 3: Cosine Similarity 90% (Production Ready) ⭐ RECOMMENDED

**When to use**: Production deployment, conservative cleanup

```bash
# 1. Install
pip install sentence-transformers scikit-learn google-genai python-docx PyPDF2 pandas

# 2. Set API key
export GEMINI_API_KEY=your-key

# 3. Run
cd approach_3_cosine_90
python prd_to_bdd_cosine_90.py
```

**Expected output**:
- `bdd_output_raw_approach3.json` - Original scenarios
- `bdd_output_deduped_approach3.json` - Cleaned (5-10% removed)
- `duplicates_report_90.csv` - Duplicate details



---

### Approach 4: LLM-Based (Highest Accuracy)

**When to use**: Critical projects, need explanations, budget available

```bash
# 1. Install (minimal dependencies)
pip install google-genai python-docx PyPDF2

# 2. Set API key
export GEMINI_API_KEY=your-key

# 3. Run
cd approach_4_llm_checking
python prd_to_bdd_llm.py
```

**Expected output**:
- `bdd_output_raw_approach4.json` - Original scenarios
- `bdd_output_deduped_approach4.json` - Cleaned (10-20% removed)


---

## 🔧 Configuration

Before running, edit the Python file and update:

```python
# Change this line in any approach file:
file_path = "prd2_macrohard.pdf"  # Update to your file

# Optional: Adjust threshold (Approaches 1, 3)
threshold = 0.9  # Change between 0.7-0.95

# Optional: Adjust batch size (Approach 4)
batch_size = 50  # Change between 20-100
```

---

## 📊 Compare All Approaches

After running multiple approaches:

```bash
# Run comparison script
python compare_approaches.py

# Generates:
# - Console output with metrics
# - comparison_report.html
```

---

## 🎓 What You'll Get

### JSON Output Format

```json
{
  "features": [
    {
      "given": "user is logged in",
      "when": "they click the logout button",
      "then": "they are logged out and redirected to homepage"
    },
    {
      "given": "user has invalid credentials",
      "when": "they attempt to login",
      "then": "they see an error message"
    }
  ]
}
```

### CSV Report Format (Approaches 1, 3)

| original_index | duplicate_index | similarity | scenario_A | scenario_B |
|----------------|-----------------|------------|------------|------------|
| 5 | 12 | 0.947 | Given user... | Given authenticated... |
| 8 | 23 | 0.923 | When payment... | When user pays... |

---

## 🆘 Troubleshooting

### Problem: ImportError
```bash
# Solution: Install missing package
pip install <package-name>
```

### Problem: API key error
```bash
# Solution: Check if key is set
echo $GEMINI_API_KEY  # Linux/Mac
echo %GEMINI_API_KEY%  # Windows

# If empty, set it:
export GEMINI_API_KEY=your-key
```

### Problem: File not found
```bash
# Solution: Use absolute path
file_path = "/full/path/to/your/prd.pdf"
```

### Problem: Out of memory (Approach 2)
```bash
# Solution: Process in smaller batches or use GPU
# Or switch to Approach 1 or 3
```

---

## 💡 Pro Tips

1. **Start with Approach 3**: Best balance of speed and accuracy
2. **Review CSV reports**: Always check what was removed
3. **Adjust thresholds**: Start conservative (0.90), then lower if needed
4. **Use hybrid approach**: Combine Approach 3 + 4 for best results
5. **Save originals**: Keep `bdd_output_raw_*.json` for rollback

---


## 🎯 Decision Flowchart

```
Need BDD scenarios?
    ↓
Is PRD redundant?
    ↓ Yes → Use Approach 1 (80%)
    ↓ No → Continue
    ↓
Production deployment?
    ↓ Yes → Use Approach 3 (90%)
    ↓ No → Continue
    ↓
Need contradiction detection?
    ↓ Yes → Use Approach 2 (NLI)
    ↓ No → Continue
    ↓
Budget for API calls?
    ↓ Yes → Use Approach 4 (LLM)
    ↓ No → Use Approach 3 (90%)
```



# -*- coding: utf-8 -*-
"""
PRD to BDD Converter - Approach 2: Cosine Similarity + NLI
Author: Arjun M S
Approach: Uses cosine similarity with Natural Language Inference for relationship detection
"""

# ==========================================================
# INSTALLATION
# ==========================================================
# !pip install sentence-transformers scikit-learn transformers torch
# !pip install google-genai python-docx PyPDF2

import docx
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import PyPDF2
from transformers import pipeline
import itertools
import torch
from tqdm import tqdm

# Import Gemini / GenAI SDK
from google import genai
from google.genai import types

# ==========================================================
# CONFIGURATION
# ==========================================================
# For Google Colab:
# from google.colab import userdata
# GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')

# For local environment:
import os
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================================
# DOCUMENT READING FUNCTIONS
# ==========================================================

def read_document(file_path):
    """
    Extracts text from a .docx or .pdf PRD file.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        str: Extracted text from the document
    """
    file_extension = Path(file_path).suffix.lower()

    if file_extension == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])
    elif file_extension == ".pdf":
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
    else:
        raise ValueError(f"Unsupported file type: {file_extension}. Please provide a .docx or .pdf file.")

    return text


def chunk_text(text, max_length=4000):
    """
    Split large documents into smaller chunks for API processing.
    
    Args:
        text: The text to split
        max_length: Maximum characters per chunk
        
    Returns:
        list: List of text chunks
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, chunk = [], ""
    
    for s in sentences:
        if len(chunk) + len(s) < max_length:
            chunk += " " + s
        else:
            chunks.append(chunk.strip())
            chunk = s
            
    if chunk:
        chunks.append(chunk.strip())
        
    return chunks


# ==========================================================
# BDD EXTRACTION FUNCTIONS
# ==========================================================

def extract_bdd_from_chunk(chunk):
    """
    Uses Gemini to extract Given/When/Then scenarios from text chunk.
    
    Args:
        chunk: Text chunk to analyze
        
    Returns:
        dict/list: Parsed BDD scenarios in JSON format
    """
    prompt = f"""
You are a software analyst. Convert the following PRD section into a structured JSON of BDD (Behavior Driven Development) scenarios.

Each scenario should be in the format:
{{
  "given": "...",
  "when": "...",
  "then": "..."
}}

If multiple features or behaviors exist, create multiple scenarios.
Keep the output strictly valid JSON (no commentary, no markdown).

Text:
{chunk}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    try:
        text_out = response.candidates[0].content.parts[0].text.strip()
    except Exception:
        text_out = response.text or ""

    # Try to parse structured output
    parsed = getattr(response, "parsed", None)
    if parsed:
        return parsed

    # If parsed is empty, use text_out fallback
    if text_out:
        cleaned = text_out.strip().strip("```json").strip("```")
        try:
            return json.loads(cleaned)
        except Exception as e:
            print("⚠️ JSON parse failed:", e)
            return {"error": "Invalid JSON", "raw_output": cleaned[:300]}
    else:
        return {"error": "Empty response"}


def prd_to_bdd_json(file_path):
    """
    Main function to convert PRD to BDD JSON format.
    
    Args:
        file_path: Path to PRD document
        
    Returns:
        dict: Complete BDD JSON with all features
    """
    text = read_document(file_path)
    chunks = chunk_text(text)

    print(f"Processing {len(chunks)} chunks...")

    all_features = []
    for i, chunk in enumerate(chunks, start=1):
        print(f"🔹 Analyzing chunk {i}/{len(chunks)}...")
        result = extract_bdd_from_chunk(chunk)

        if result is None:
            print(f"⚠️ Chunk {i} returned None – skipping")
            continue

        # Handle different possible output formats from the LLM
        if isinstance(result, dict) and "features" in result:
            all_features.extend(result["features"])
        elif isinstance(result, list):
            all_features.extend(result)
        else:
            all_features.append(result)

    bdd_data = {"features": all_features}
    return bdd_data


# ==========================================================
# DEDUPLICATION: APPROACH 2 - COSINE SIMILARITY + NLI
# ==========================================================

def analyze_bdd_steps_with_nli(bdd_features):
    """
    Analyze BDD scenarios using Cosine Similarity + Natural Language Inference.
    
    This function:
    1. Extracts individual Given/When/Then steps
    2. Computes semantic embeddings
    3. Calculates cosine similarity
    4. Uses NLI model to classify relationships (entailment/contradiction/neutral)
    
    Args:
        bdd_features: List of BDD feature dictionaries
        
    Returns:
        tuple: (DataFrame with analysis results, list of BDD steps)
    """
    # Extract individual BDD steps
    bdd_steps = []
    for feature in bdd_features:
        for key in ["given", "when", "then"]:
            text = feature.get(key)
            if text:
                bdd_steps.append(f"{key.capitalize()}: {text}")

    print(f"✅ Extracted {len(bdd_steps)} total BDD steps for comparison.\n")

    # Setup device and models
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}\n")

    embedder = SentenceTransformer('all-mpnet-base-v2', device=device)
    nli_model = pipeline(
        "text-classification", 
        model="roberta-large-mnli", 
        device=0 if device == 'cuda' else -1
    )

    # Generate all unique pairs
    pairs = list(itertools.combinations(bdd_steps, 2))
    print(f"Total pairs to compare: {len(pairs)}")

    # Cache embeddings once
    print("Encoding all steps once for efficiency...")
    embeddings = embedder.encode(bdd_steps, convert_to_tensor=True)
    print("✅ Embeddings ready.\n")

    results = []

    # Precompute all cosine similarities
    cosine_matrix = util.pytorch_cos_sim(embeddings, embeddings)

    # Loop through pairs with progress bar
    for i, (s1, s2) in enumerate(tqdm(pairs, desc="Comparing pairs")):
        idx1 = bdd_steps.index(s1)
        idx2 = bdd_steps.index(s2)
        sim_score = cosine_matrix[idx1][idx2].item()

        # Only run NLI if sentences are somewhat similar (saves time)
        if sim_score > 0.6:
            nli_input = s1 + " </s> " + s2
            nli_result = nli_model(nli_input)[0]
            label, conf = nli_result['label'], nli_result['score']
        else:
            label, conf = "NEUTRAL", 1.0

        # Decision logic
        if sim_score > 0.8:
            if label == 'ENTAILMENT':
                decision = "✅ Likely Duplicate"
            elif label == 'CONTRADICTION':
                decision = "❌ Contradictory"
            else:
                decision = "⚠️ Similar but Unclear"
        else:
            decision = "❌ Not Similar"

        results.append({
            'Step 1': s1,
            'Step 2': s2,
            'Similarity': round(sim_score, 4),
            'NLI Label': label,
            'Confidence': round(conf * 100, 2),
            'Decision': decision
        })

    # Create results dataframe
    df_results = pd.DataFrame(results)
    return df_results, bdd_steps


# ==========================================================
# MAIN EXECUTION
# ==========================================================

if __name__ == "__main__":
    # Specify your PRD file path
    file_path = "prd2_macrohard.pdf"  # Change this to your file
    
    print("=" * 60)
    print("APPROACH 2: COSINE SIMILARITY + NLI")
    print("=" * 60)
    
    # Generate BDD scenarios
    bdd_json = prd_to_bdd_json(file_path)
    print(f"\n📊 Generated {len(bdd_json['features'])} initial scenarios")

    # Save before deduplication
    raw_output_path = Path("bdd_output_raw_approach2.json")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump(bdd_json, f, indent=2, ensure_ascii=False)
    print(f"📁 Saved original (before deduplication): {raw_output_path.resolve()}")

    # Perform NLI analysis
    print("\n" + "=" * 60)
    print("PERFORMING NLI ANALYSIS")
    print("=" * 60 + "\n")
    
    df_results, bdd_steps = analyze_bdd_steps_with_nli(bdd_json['features'])
    
    # Display summary statistics
    total_count = len(bdd_steps)
    duplicate_count = df_results[df_results['Decision'] == '✅ Likely Duplicate'].shape[0]
    contradicting_count = df_results[df_results['Decision'] == '❌ Contradictory'].shape[0]
    
    print(f"\n--- Summary of BDD Step Analysis ---")
    print(f"Total individual steps analyzed: {total_count}")
    print(f"Pairs identified as Likely Duplicates: {duplicate_count}")
    print(f"Pairs identified as Contradictory: {contradicting_count}")
    print(f"Number of scenarios before cleanup: {len(bdd_json['features'])}")
    print(f"------------------------------------")
    
    # Save detailed results to CSV
    output_csv = "nli_comparison_results.csv"
    df_results.to_csv(output_csv, index=False)
    print(f"\n✅ Detailed analysis saved to '{output_csv}'")
    
    # Save final JSON (note: this approach is for analysis, not automatic deduplication)
    print(f"\n📁 Saved analysis results.")
    print(f"📊 Review the CSV file to manually decide which scenarios to keep/remove.")
    
    print(f"\n✅ Processing complete!")

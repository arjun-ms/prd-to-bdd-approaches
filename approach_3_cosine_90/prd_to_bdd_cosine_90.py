# -*- coding: utf-8 -*-
"""
PRD to BDD Converter - Approach 3: Cosine Similarity (90% Threshold)
Author: Arjun M S
Approach: Uses cosine similarity with 90% threshold and predefined contrast pairs
"""

# ==========================================================
# INSTALLATION
# ==========================================================
# !pip install sentence-transformers scikit-learn
# !pip install google-genai python-docx PyPDF2

import docx
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import PyPDF2
from textwrap import shorten

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
        print("=== CLEANED RESPONSE ===")
        print(cleaned)
        print("====================\n")
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
# DEDUPLICATION: APPROACH 3 - COSINE SIMILARITY (90%)
# ==========================================================

def remove_duplicates_cosine_90(features, threshold=0.9, show_duplicates=True):
    """
    Remove semantically similar BDD scenarios using cosine similarity 
    with 90% threshold and contrast pair detection.
    
    This is the most conservative approach - only removes very similar scenarios.
    
    Args:
        features: List of BDD feature dictionaries
        threshold: Similarity threshold (default: 0.9)
        show_duplicates: Whether to show duplicate pairs
        
    Returns:
        list: Deduplicated list of features
    """
    model = SentenceTransformer('intfloat/e5-large-v2')

    texts = [
        f"Given {f.get('given', '')} When {f.get('when', '')} Then {f.get('then', '')}"
        for f in features
    ]

    # Extract When and Then texts separately for contrast check
    whens = [f.get('when', '') for f in features]
    thens = [f.get('then', '') for f in features]

    embeddings = model.encode(texts)
    sim_matrix = cosine_similarity(embeddings)

    seen = set()
    unique_indices = []
    duplicates = []

    # Define contradictory keyword pairs (extended list)
    contrast_pairs = [
        ("success", "error"), ("approve", "reject"),
        ("completed", "failed"), ("allow", "deny"),
        ("green", "red"), ("enabled", "disabled"),
        ("true", "false"), ("valid", "invalid"),
        ("accepted", "rejected"), ("active", "inactive"),
        ("pass", "fail"), ("positive", "negative"),
        ("granted", "denied"), ("authenticated", "unauthorized")
    ]

    def has_contrast(text1, text2):
        """Check if two texts contain contradictory keywords."""
        t1, t2 = text1.lower(), text2.lower()
        for a, b in contrast_pairs:
            if (a in t1 and b in t2) or (b in t1 and a in t2):
                return True
        return False

    for i in range(len(features)):
        if i in seen:
            continue
        for j in range(i + 1, len(features)):
            # Check for both similarity and lack of contrast
            if sim_matrix[i, j] > threshold and not has_contrast(
                f"{whens[i]} {thens[i]}", f"{whens[j]} {thens[j]}"
            ):
                seen.add(j)
                duplicates.append((i, j, sim_matrix[i, j]))
        unique_indices.append(i)

    removed_count = len(features) - len(unique_indices)
    print(f"\n🧹 Before cleanup: {len(features)} scenarios")
    print(f"❌🗑️ Removed {removed_count} DUPLICATE SCENARIOS.")
    print(f"✅ After cleanup: {len(unique_indices)} scenarios\n")

    if show_duplicates and duplicates:
        print("🔍 Duplicate scenario pairs (showing top 10 by similarity):\n")
        duplicates = sorted(duplicates, key=lambda x: x[2], reverse=True)

        for i, (a, b, score) in enumerate(duplicates[:10]):
            print(f"\n🧩 Similarity: {score:.3f}")
            print(f"🅰️ Scenario A: {texts[a][:300]}")
            print(f"🅱️ Scenario B: {texts[b][:300]}")
            print("-" * 80)

    # Save to CSV for later inspection
    if show_duplicates and duplicates:
        dup_data = [
            {"original_index": a, "duplicate_index": b, "similarity": score,
             "scenario_A": texts[a], "scenario_B": texts[b]}
            for a, b, score in duplicates
        ]
        pd.DataFrame(dup_data).to_csv("duplicates_report_90.csv", index=False, encoding="utf-8")
        print("\n📊 Detailed duplicate report saved → duplicates_report_90.csv")

    return [features[i] for i in unique_indices]


# ==========================================================
# MAIN EXECUTION
# ==========================================================

if __name__ == "__main__":
    # Specify your PRD file path
    file_path = "prd2_macrohard.pdf"  # Change this to your file
    
    print("=" * 60)
    print("APPROACH 3: COSINE SIMILARITY (90% THRESHOLD)")
    print("=" * 60)
    
    # Generate BDD scenarios
    bdd_json = prd_to_bdd_json(file_path)
    print(f"\n📊 Generated {len(bdd_json['features'])} initial scenarios")

    # Save before deduplication
    raw_output_path = Path("bdd_output_raw_approach3.json")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump(bdd_json, f, indent=2, ensure_ascii=False)
    print(f"📁 Saved original (before deduplication): {raw_output_path.resolve()}")

    # Remove duplicates using 90% threshold
    bdd_json["features"] = remove_duplicates_cosine_90(
        bdd_json["features"], 
        threshold=0.9
    )

    # Save after deduplication
    deduped_output_path = Path("bdd_output_deduped_approach3.json")
    with open(deduped_output_path, "w", encoding="utf-8") as f:
        json.dump(bdd_json, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Saved cleaned (after deduplication): {deduped_output_path.resolve()}")

    print(f"\n✅ Processing complete!")
    print(f"📊 Final count: {len(bdd_json['features'])} unique scenarios")

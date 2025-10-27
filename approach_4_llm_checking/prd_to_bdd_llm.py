# -*- coding: utf-8 -*-
"""
PRD to BDD Converter - Approach 4: LLM-Based Duplicate Checking
Author: Arjun M S
Approach: Uses LLM to intelligently identify and remove semantic duplicates
"""

# ==========================================================
# INSTALLATION
# ==========================================================
# !pip install google-genai python-docx PyPDF2

import docx
import json
import re
from pathlib import Path
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
# DEDUPLICATION: APPROACH 4 - LLM-BASED CHECKING
# ==========================================================

def clean_duplicates_with_llm(bdd_json_data, client, batch_size=50):
    """
    Uses an LLM to intelligently identify and remove duplicate BDD scenarios.
    
    This approach:
    1. Processes scenarios in batches to avoid token limits
    2. Uses LLM's semantic understanding to identify duplicates
    3. Preserves important variations and opposite test cases
    4. Provides explanations for removal decisions
    
    Args:
        bdd_json_data: Dictionary with 'features' key containing BDD scenarios
        client: Gemini API client
        batch_size: Number of scenarios to process per batch
        
    Returns:
        dict: Cleaned BDD data with duplicates removed
    """
    features = bdd_json_data.get("features", [])
    total_features = len(features)
    
    if total_features == 0:
        return bdd_json_data
    
    print(f"\n🤖 Starting LLM-based deduplication...")
    print(f"📊 Total scenarios to analyze: {total_features}")
    print(f"📦 Batch size: {batch_size}\n")
    
    all_unique_features = []
    removed_count = 0
    
    # Process in batches to avoid token limits
    for batch_num, i in enumerate(range(0, total_features, batch_size), 1):
        batch = features[i:i+batch_size]
        batch_size_actual = len(batch)
        
        print(f"🔄 Processing batch {batch_num} ({batch_size_actual} scenarios)...")
        
        prompt = f"""
You are a software quality analyst tasked with reviewing BDD (Behavior Driven Development) scenarios for duplicates.

Your goal is to identify and remove scenarios that are semantically duplicate or very similar to others in the list.

IMPORTANT RULES:
1. Consider scenarios duplicates if they describe the SAME behavior or requirement, even if worded differently
2. DO NOT remove scenarios that test opposite outcomes (e.g., success vs. error cases)
3. DO NOT remove scenarios that test different user roles or permissions
4. DO NOT remove scenarios that test different input variations (valid vs. invalid)
5. PRESERVE edge cases and boundary conditions
6. Keep scenarios that test the same feature but with different preconditions

For each scenario, decide whether to KEEP or REMOVE it.
If removing, briefly explain why it's a duplicate of which other scenario.

Input JSON with {batch_size_actual} scenarios:
{json.dumps(batch, indent=2, ensure_ascii=False)}

Output JSON format:
{{
  "features": [
    {{
      "given": "...",
      "when": "...",
      "then": "...",
      "action": "keep"
    }}
  ],
  "removed": [
    {{
      "given": "...",
      "when": "...",
      "then": "...",
      "reason": "Duplicate of scenario X - same behavior"
    }}
  ]
}}

Return only valid JSON, no commentary.
"""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",  # Using more capable model for analysis
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1  # Low temperature for consistent decisions
                )
            )

            try:
                text_out = response.candidates[0].content.parts[0].text.strip()
            except Exception:
                text_out = response.text or ""

            # Try to parse structured output
            parsed = getattr(response, "parsed", None)
            if parsed:
                result = parsed
            elif text_out:
                cleaned = text_out.strip().strip("```json").strip("```")
                result = json.loads(cleaned)
            else:
                print(f"⚠️ Batch {batch_num} returned empty response - keeping all")
                all_unique_features.extend(batch)
                continue

            # Extract kept features
            kept = result.get("features", [])
            removed = result.get("removed", [])
            
            # Add kept scenarios to results
            all_unique_features.extend(kept)
            removed_count += len(removed)
            
            print(f"  ✅ Kept: {len(kept)}, ❌ Removed: {len(removed)}")
            
            # Show removal reasons for first few
            if removed and batch_num <= 3:
                print(f"  📝 Sample removals:")
                for item in removed[:3]:
                    reason = item.get("reason", "No reason provided")
                    scenario_preview = f"{item.get('when', '')[:50]}..."
                    print(f"     • {scenario_preview} → {reason}")
            
        except Exception as e:
            print(f"⚠️ Error processing batch {batch_num}: {e}")
            print(f"   Keeping all scenarios in this batch")
            all_unique_features.extend(batch)
    
    print(f"\n{'='*60}")
    print(f"🧹 Deduplication Summary")
    print(f"{'='*60}")
    print(f"📊 Original scenarios: {total_features}")
    print(f"✅ Scenarios kept: {len(all_unique_features)}")
    print(f"❌ Scenarios removed: {removed_count}")
    print(f"📉 Removal rate: {(removed_count/total_features*100):.1f}%")
    print(f"{'='*60}\n")
    
    return {"features": all_unique_features}


# ==========================================================
# MAIN EXECUTION
# ==========================================================

if __name__ == "__main__":
    # Specify your PRD file path
    file_path = "prd2_macrohard.pdf"  # Change this to your file
    
    print("=" * 60)
    print("APPROACH 4: LLM-BASED DUPLICATE CHECKING")
    print("=" * 60)
    
    # Generate BDD scenarios
    bdd_json = prd_to_bdd_json(file_path)
    print(f"\n📊 Generated {len(bdd_json['features'])} initial scenarios")

    # Save before deduplication
    raw_output_path = Path("bdd_output_raw_approach4.json")
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump(bdd_json, f, indent=2, ensure_ascii=False)
    print(f"📁 Saved original (before deduplication): {raw_output_path.resolve()}")

    # Remove duplicates using LLM
    print("\n" + "=" * 60)
    print("PERFORMING LLM-BASED DEDUPLICATION")
    print("=" * 60)
    
    cleaned_bdd_json = clean_duplicates_with_llm(
        bdd_json, 
        client,
        batch_size=50  # Adjust based on your scenario complexity
    )

    # Save after deduplication
    deduped_output_path = Path("bdd_output_deduped_approach4.json")
    with open(deduped_output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_bdd_json, f, indent=2, ensure_ascii=False)
    print(f"📁 Saved cleaned (after deduplication): {deduped_output_path.resolve()}")

    print(f"\n✅ Processing complete!")
    print(f"📊 Final count: {len(cleaned_bdd_json['features'])} unique scenarios")

# """
# Comparison Script for All PRD to BDD Approaches
# Author: Arjun M S

# This script helps you compare results from different approaches side-by-side.
# """

# import json
# from pathlib import Path
# import pandas as pd
# from typing import Dict, List


# def load_json(filepath: str) -> Dict:
#     """Load a JSON file."""
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return None


# def analyze_approach(approach_name: str, raw_file: str, deduped_file: str) -> Dict:
#     """Analyze a single approach's results."""
#     raw_data = load_json(raw_file)
#     deduped_data = load_json(deduped_file)
    
#     if not raw_data or not deduped_data:
#         return {
#             'approach': approach_name,
#             'status': 'Files not found',
#             'original_count': 0,
#             'final_count': 0,
#             'removed': 0,
#             'removal_rate': 0
#         }
    
#     original_count = len(raw_data.get('features', []))
#     final_count = len(deduped_data.get('features', []))
#     removed = original_count - final_count
#     removal_rate = (removed / original_count * 100) if original_count > 0 else 0
    
#     return {
#         'approach': approach_name,
#         'status': 'Success',
#         'original_count': original_count,
#         'final_count': final_count,
#         'removed': removed,
#         'removal_rate': round(removal_rate, 2)
#     }


# def compare_all_approaches(base_path: str = "."):
#     """Compare all four approaches."""
#     approaches = [
#         {
#             'name': 'Approach 1: Cosine 80%',
#             'raw': f'{base_path}/approach_1_cosine_80/bdd_output_raw_approach1.json',
#             'deduped': f'{base_path}/approach_1_cosine_80/bdd_output_deduped_approach1.json'
#         },
#         {
#             'name': 'Approach 2: Cosine + NLI',
#             'raw': f'{base_path}/approach_2_cosine_nli/bdd_output_raw_approach2.json',
#             'deduped': 'Analysis only - no automatic deduplication'
#         },
#         {
#             'name': 'Approach 3: Cosine 90%',
#             'raw': f'{base_path}/approach_3_cosine_90/bdd_output_raw_approach3.json',
#             'deduped': f'{base_path}/approach_3_cosine_90/bdd_output_deduped_approach3.json'
#         },
#         {
#             'name': 'Approach 4: LLM-Based',
#             'raw': f'{base_path}/approach_4_llm_checking/bdd_output_raw_approach4.json',
#             'deduped': f'{base_path}/approach_4_llm_checking/bdd_output_deduped_approach4.json'
#         }
#     ]
    
#     results = []
    
#     print("=" * 80)
#     print("PRD TO BDD - APPROACH COMPARISON")
#     print("=" * 80)
#     print()
    
#     for approach in approaches:
#         if approach['deduped'] == 'Analysis only - no automatic deduplication':
#             # Special handling for Approach 2
#             raw_data = load_json(approach['raw'])
#             if raw_data:
#                 results.append({
#                     'approach': approach['name'],
#                     'status': 'Analysis Only',
#                     'original_count': len(raw_data.get('features', [])),
#                     'final_count': 'N/A',
#                     'removed': 'N/A',
#                     'removal_rate': 'N/A'
#                 })
#         else:
#             result = analyze_approach(approach['name'], approach['raw'], approach['deduped'])
#             results.append(result)
    
#     # Create DataFrame for nice display
#     df = pd.DataFrame(results)
    
#     print(df.to_string(index=False))
#     print()
#     print("=" * 80)
    
#     # Additional statistics
#     print("\nKEY INSIGHTS:")
#     print("-" * 80)
    
#     removal_rates = [r['removal_rate'] for r in results if isinstance(r['removal_rate'], (int, float))]
    
#     if removal_rates:
#         most_aggressive = max(results, key=lambda x: x['removal_rate'] if isinstance(x['removal_rate'], (int, float)) else 0)
#         most_conservative = min(results, key=lambda x: x['removal_rate'] if isinstance(x['removal_rate'], (int, float)) else 100)
        
#         print(f"\n🔥 Most Aggressive: {most_aggressive['approach']}")
#         print(f"   Removed: {most_aggressive['removed']} scenarios ({most_aggressive['removal_rate']}%)")
        
#         print(f"\n🛡️  Most Conservative: {most_conservative['approach']}")
#         print(f"   Removed: {most_conservative['removed']} scenarios ({most_conservative['removal_rate']}%)")
        
#         avg_removal = sum(removal_rates) / len(removal_rates)
#         print(f"\n📊 Average Removal Rate: {avg_removal:.2f}%")
    
#     print("\n" + "=" * 80)
    
#     return df


# def compare_scenario_overlap(approach1_file: str, approach2_file: str):
#     """Compare which scenarios are kept/removed between two approaches."""
#     data1 = load_json(approach1_file)
#     data2 = load_json(approach2_file)
    
#     if not data1 or not data2:
#         print("Error: Could not load files for comparison")
#         return
    
#     # Create sets of scenario strings for comparison
#     scenarios1 = set([
#         f"{f.get('given', '')}|{f.get('when', '')}|{f.get('then', '')}"
#         for f in data1.get('features', [])
#     ])
    
#     scenarios2 = set([
#         f"{f.get('given', '')}|{f.get('when', '')}|{f.get('then', '')}"
#         for f in data2.get('features', [])
#     ])
    
#     common = scenarios1.intersection(scenarios2)
#     only_in_1 = scenarios1 - scenarios2
#     only_in_2 = scenarios2 - scenarios1
    
#     print("\n" + "=" * 80)
#     print("SCENARIO OVERLAP ANALYSIS")
#     print("=" * 80)
#     print(f"\n✅ Scenarios kept by both approaches: {len(common)}")
#     print(f"🔴 Scenarios only in Approach 1: {len(only_in_1)}")
#     print(f"🔵 Scenarios only in Approach 2: {len(only_in_2)}")
    
#     overlap_percentage = (len(common) / len(scenarios1) * 100) if len(scenarios1) > 0 else 0
#     print(f"\n📊 Overlap: {overlap_percentage:.2f}%")
    
#     if only_in_1:
#         print(f"\n📝 Sample scenarios removed by Approach 2 but kept by Approach 1:")
#         for scenario in list(only_in_1)[:3]:
#             parts = scenario.split('|')
#             print(f"\n  Given: {parts[0][:60]}...")
#             print(f"  When:  {parts[1][:60]}...")
#             print(f"  Then:  {parts[2][:60]}...")


# def generate_html_report(base_path: str = "."):
#     """Generate an HTML report comparing all approaches."""
#     approaches_data = compare_all_approaches(base_path)
    
#     html = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>PRD to BDD Comparison Report</title>
#         <style>
#             body { font-family: Arial, sans-serif; margin: 40px; }
#             h1 { color: #333; }
#             table { border-collapse: collapse; width: 100%; margin-top: 20px; }
#             th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
#             th { background-color: #4CAF50; color: white; }
#             tr:nth-child(even) { background-color: #f2f2f2; }
#             .insight { background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-left: 4px solid #2196F3; }
#         </style>
#     </head>
#     <body>
#         <h1>PRD to BDD Approach Comparison Report</h1>
#         <p>Generated: <strong>""" + str(pd.Timestamp.now()) + """</strong></p>
        
#         <div class="insight">
#             <h3>📊 Quick Summary</h3>
#             <p>This report compares four different approaches for detecting and removing duplicate BDD scenarios.</p>
#         </div>
        
#         """ + approaches_data.to_html(index=False) + """
        
#         <div class="insight">
#             <h3>💡 Recommendations</h3>
#             <ul>
#                 <li><strong>For Production:</strong> Use Approach 3 (90% threshold) for best precision</li>
#                 <li><strong>For Prototyping:</strong> Use Approach 1 (80% threshold) for faster cleanup</li>
#                 <li><strong>For Research:</strong> Use Approach 2 (NLI) for detailed analysis</li>
#                 <li><strong>For Critical Projects:</strong> Use Approach 4 (LLM) when accuracy is paramount</li>
#             </ul>
#         </div>
#     </body>
#     </html>
#     """
    
#     with open('comparison_report.html', 'w', encoding='utf-8') as f:
#         f.write(html)
    
#     print("\n✅ HTML report generated: comparison_report.html")


# if __name__ == "__main__":
#     import sys
    
#     # Get base path from command line or use current directory
#     base_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
#     # Run comparison
#     compare_all_approaches(base_path)
    
#     # Generate HTML report
#     generate_html_report(base_path)
    
#     # Example: Compare two specific approaches
#     print("\n" + "=" * 80)
#     print("DETAILED COMPARISON: Approach 1 vs Approach 3")
#     print("=" * 80)
#     compare_scenario_overlap(
#         f'{base_path}/approach_1_cosine_80/bdd_output_deduped_approach1.json',
#         f'{base_path}/approach_3_cosine_90/bdd_output_deduped_approach3.json'
#     )

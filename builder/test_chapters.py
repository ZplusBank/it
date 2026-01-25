#!/usr/bin/env python3
"""Quick test to verify all chapters are loaded correctly"""

import json
from pathlib import Path

base_path = Path(__file__).parent.parent
data_path = base_path / "data"
java2_path = data_path / "java2"

print("📚 Chapter Detection Test\n")
print(f"Scanning: {java2_path}\n")

chapters = []
total_questions = 0

for json_file in sorted(java2_path.glob("*.json")):
    if json_file.name == "chapters.json":
        continue
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle both array and object formats
            if isinstance(data, list):
                obj = data[0] if len(data) > 0 else {}
            else:
                obj = data
            
            # Get totalQuestions
            question_count = obj.get('totalQuestions', None)
            if question_count is None:
                questions = obj.get('questions', [])
                question_count = len(questions)
            
            title = obj.get('title', json_file.stem)
            chapters.append({
                'file': json_file.name,
                'title': title,
                'questions': question_count
            })
            total_questions += question_count
            
            print(f"✓ {json_file.name:20} | {title:50} | {question_count} questions")
    except Exception as e:
        print(f"✗ {json_file.name:20} | Error: {e}")

print(f"\n{'='*90}")
print(f"Total: {len(chapters)} chapters | {total_questions} questions")
print(f"{'='*90}")

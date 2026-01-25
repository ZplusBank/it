import json
from pathlib import Path
import re

def setup():
    base_path = Path(__file__).parent.parent
    data_path = base_path / "data"
    config_path = base_path / "config"
    
    # 1. Create Directories and chapters.json
    new_sections = ["java1", "algorithm", "data_structure", "java_advanced"]
    
    for section in new_sections:
        sec_path = data_path / section
        sec_path.mkdir(parents=True, exist_ok=True)
        chapters_file = sec_path / "chapters.json"
        if not chapters_file.exists():
            with open(chapters_file, 'w') as f:
                json.dump([], f)
            print(f"Created {section} structure")

    # 2. Scan properties of java2 and generate chapters.json
    java2_path = data_path / "java2"
    java2_chapters = []
    
    if java2_path.exists():
        chapter_files = sorted(java2_path.glob("chapter*.json"))
        # Sort by number in filename
        def get_chapter_num(path):
            match = re.search(r'chapter(\d+)', path.name)
            return int(match.group(1)) if match else 999
            
        chapter_files.sort(key=get_chapter_num)
        
        for ch_file in chapter_files:
            try:
                with open(ch_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                    if isinstance(content, list):
                         print(f"Skipping {ch_file.name}: Content is a list, expected dict")
                         continue
                         
                    # Extract info for index
                    ch_info = {
                        "id": str(content.get("params", {}).get("chapter", "")),
                        "name": content.get("title", "").replace(f"Chapter {content.get('params', {}).get('chapter', '')} ", ""),
                        "q": len(content.get("questions", [])),
                        "file": ch_file.name
                    }
                    java2_chapters.append(ch_info)
            except Exception as e:
                try:
                    print(f"Error reading {ch_file.name}: {e}")
                except:
                    print(f"Error reading file (name encoding issue): {e}")
        
        # Write java2 chapters.json
        with open(java2_path / "chapters.json", 'w') as f:
            json.dump(java2_chapters, f, indent=2)
        print(f"Generated java2/chapters.json with {len(java2_chapters)} chapters")

    # 3. Create config/sections.json
    config_path.mkdir(exist_ok=True)
    
    sections_config = [
        {"id": "java1", "name": "Java 1", "path": "data/java1", "description": "Introduction to Java"},
        {"id": "java2", "name": "Java 2", "path": "data/java2", "description": "Advanced Java"},
        {"id": "algorithm", "name": "Algorithms", "path": "data/algorithm", "description": "Algorithm Analysis"},
        {"id": "data_structure", "name": "Data Structures", "path": "data/data_structure", "description": "Data Structures"},
        {"id": "java_advanced", "name": "Java Advanced", "path": "data/java_advanced", "description": "Enterprise Java"}
    ]
    
    with open(config_path / "sections.json", 'w') as f:
        json.dump(sections_config, f, indent=2)
    print("Created config/sections.json")

if __name__ == "__main__":
    setup()

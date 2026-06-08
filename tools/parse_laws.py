import os
import re
import json

def parse_law_file(filepath):
    """Parse một file luật từ Victoria 3 wiki format"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    category = os.path.basename(filepath).replace('.txt', '')
    laws = {}
    
    # Tìm tất cả các law blocks (bắt đầu bằng |- id="..." hoặc {{iconbox|...)
    # Pattern cho iconbox
    iconbox_pattern = r'\{\{iconbox\|([^|]+)\|([^}]+)\}\}'
    
    # Tìm các section
    rows = content.split('|-')
    
    for row in rows:
        if '{{iconbox' not in row:
            continue
            
        # Lấy tên luật
        icon_match = re.search(iconbox_pattern, row)
        if not icon_match:
            continue
            
        law_name = icon_match.group(1).strip()
        law_desc = icon_match.group(2).strip()
        
        # Lấy effects (các dòng bắt đầu bằng * hoặc {{green|...}})
        effects = []
        for line in row.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                effect = line[1:].strip()
                # Dọn dẹp các ký tự wiki
                effect = re.sub(r'\{\{[^|]+\|([^}]+)[^}]*\}\}', r'\1', effect)
                effect = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', effect)
                effect = effect.replace("'''", "").replace("''", "").strip()
                if effect and len(effect) > 2:
                    effects.append(effect[:80])  # Giới hạn độ dài
            elif '{{green|' in line or '{{red|' in line:
                effect = re.sub(r'\{\{(green|red)\|([^}]+)\}\}', r'\2', line)
                effect = effect.strip()
                if effect and len(effect) > 2:
                    effects.append(effect[:80])
        
        # Lấy requirements
        requirements = []
        req_section = re.search(r'\|.*?Requirements.*?\n(.*?)\n\|', row, re.DOTALL)
        if req_section:
            req_text = req_section.group(1)
            for line in req_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('|') and not line.startswith('{{'):
                    clean = re.sub(r'\{\{[^}]+\}\}', '', line).strip()
                    if clean and len(clean) > 3:
                        requirements.append(clean[:60])
        
        # Lấy stance của interest groups
        stances = {}
        stance_pattern = r'\{\{icon\|(\w+)\|3=1\}\}\s*\{\{(green|red|neutral)\|(.*?)\}\}'
        for stance_match in re.finditer(stance_pattern, row):
            ig = stance_match.group(1)
            stance_type = stance_match.group(2)
            stance_text = stance_match.group(3).strip()
            stances[ig] = {"type": stance_type, "text": stance_text}
        
        laws[law_name] = {
            "category": category,
            "desc": law_desc[:120],
            "requirements": requirements[:2],
            "effects": effects[:3],
            "stances": stances
        }
    
    return category, laws

def convert_all_laws(data_dir="data/laws", output_file="data/laws/laws_compiled.json"):
    """Chuyển đổi tất cả file txt trong thư mục laws thành JSON"""
    all_laws = {}
    
    for filename in os.listdir(data_dir):
        if not filename.endswith('.txt'):
            continue
        if filename == 'laws.json':  # Bỏ qua file JSON cũ
            continue
            
        filepath = os.path.join(data_dir, filename)
        print(f"Parsing: {filename}")
        
        try:
            category, laws = parse_law_file(filepath)
            all_laws.update(laws)
            print(f"  -> Found {len(laws)} laws in {category}")
        except Exception as e:
            print(f"  -> Error parsing {filename}: {e}")
    
    # Lưu vào file JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_laws, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(all_laws)} laws to {output_file}")
    return all_laws

if __name__ == "__main__":
    # Chạy từ thư mục gốc của project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    laws_dir = os.path.join(base_dir, "data", "laws")
    output_path = os.path.join(laws_dir, "laws_compiled.json")
    
    convert_all_laws(laws_dir, output_path)
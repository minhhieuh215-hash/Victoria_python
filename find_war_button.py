import json

log_path = r"C:\Users\Admin\.gemini\antigravity\brain\fc696c0c-0418-4319-a641-267c52adf07d\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f):
        if "⚔️ war panel" in line.lower():
            try:
                data = json.loads(line)
                step_idx = data.get("step_index", line_num)
                print(f"Step {step_idx}: type={data.get('type')}, size={len(line)}")
                # If there are tool calls, print their args
                for tc in data.get("tool_calls", []):
                    print(f"  args: {json.dumps(tc.get('args'), indent=2, ensure_ascii=False)[:500]}")
            except:
                pass

import os

logs = [
    r"C:\Users\Admin\.gemini\antigravity\brain\1144ec52-be06-4c92-b2bc-aae32a763c12\.system_generated\logs\transcript.jsonl",
    r"C:\Users\Admin\.gemini\antigravity\brain\6ea7d11b-6aee-4052-a720-a686c6ab3bc8\.system_generated\logs\transcript.jsonl",
    r"C:\Users\Admin\.gemini\antigravity\brain\fc696c0c-0418-4319-a641-267c52adf07d\.system_generated\logs\transcript.jsonl"
]

for log in logs:
    print(f"Exists {log}: {os.path.exists(log)}")

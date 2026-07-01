import os, sys, json
from pathlib import Path
from backend.core.settings import get_settings
from backend.llm.client import LLMClient

print('=== Phase 1: Preflight Verification ===')

settings = get_settings()
print(f'1. Environment Settings Loaded')
print(f'   Provider: {settings.LLM_PROVIDER}')

if not Path('data/raw/candidates.jsonl').exists():
    print('Dataset missing!')
    sys.exit(1)
print(f'2. Dataset Exists')

if not Path('data/index/faiss.index').exists():
    print('FAISS index missing!')
    sys.exit(1)
print(f'3. FAISS Index Exists')

with open('data/index/metadata.json') as f:
    meta = json.load(f)
    print(f'4. Cache metadata loaded, next_id={meta.get("next_id")}')

out_dir = Path('output')
out_dir.mkdir(exist_ok=True)
print(f'5. Output directory available')

print(f'6. Checking LLM Provider Health...')
client = LLMClient()
try:
    if client.provider.health_check():
        print(f'   Provider {client.provider.__class__.__name__} is HEALTHY')
    else:
        print(f'   Provider health check failed!')
        sys.exit(1)
except Exception as e:
    print(f'   Health check exception: {e}')
    sys.exit(1)

print('ALL PREFLIGHT CHECKS PASSED.')

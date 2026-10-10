import re
import os
import sys

def audit():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, 'frontend', 'index.html')
    js_path = os.path.join(base_dir, 'frontend', 'app.js')

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    with open(js_path, 'r', encoding='utf-8') as f:
        js = f.read()

    # Find all event handlers in HTML
    events = re.findall(r'on(?:click|change|input|keydown)=["\']([^"\']+)["\']', html)
    print(f"Total event bindings found in index.html: {len(events)}")
    
    unique_calls = set()
    for ev in events:
        m = re.match(r'([a-zA-Z0-9_]+)\s*\(', ev)
        if m:
            unique_calls.add(m.group(1))

    print(f"Unique functions invoked from HTML: {len(unique_calls)}")
    missing = []
    for fn in sorted(unique_calls):
        pattern = rf'function\s+{fn}\b|const\s+{fn}\s*=|let\s+{fn}\s*=|window\.{fn}\s*='
        if not re.search(pattern, js):
            missing.append(fn)

    if missing:
        print(f"WARNING: The following {len(missing)} functions are bound in index.html but NOT defined in app.js:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("ALL functions bound in index.html are defined in app.js!")

    # Check for empty element IDs referenced in JS
    js_ids = re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', js)
    print(f"\nTotal document.getElementById calls in app.js: {len(js_ids)}")
    missing_ids = []
    for el_id in sorted(set(js_ids)):
        if f'id="{el_id}"' not in html and f"id='{el_id}'" not in html:
            missing_ids.append(el_id)
            
    if missing_ids:
        print(f"WARNING: The following {len(missing_ids)} IDs are referenced in app.js but NOT found in index.html:")
        for mid in missing_ids:
            print(f"  - {mid}")
    else:
        print("ALL getElementById references in app.js match IDs in index.html!")

if __name__ == '__main__':
    audit()

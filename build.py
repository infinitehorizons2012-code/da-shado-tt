import json
import re

with open('public/data.json', 'r', encoding='utf-8') as f:
    data_json = f.read()
    data_obj = json.loads(data_json)
    
video_url = data_obj.get('video_url', '')
match = re.search(r'/([^/]+)\.mp4', video_url)
video_name = match.group(1) if match else 'commercial_build'

with open('public/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the fetch logic with inline data
fetch_pattern = r"const response = await fetch\('data\.json\?v=' \+ new Date\(\)\.getTime\(\)\);\s*if \(!response\.ok\) throw new Error\('Cannot load data'\);\s*const data = await response\.json\(\);"

replacement = f"const data = {data_json};"

new_html = re.sub(fetch_pattern, replacement, html)

output_filename = f"{video_name}.html"
with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"Successfully generated {output_filename}")

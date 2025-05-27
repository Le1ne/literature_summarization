import json
import os

clean_folder = 'processed_annotations'
raw_folder = 'texts'

clean_files = os.listdir(clean_folder)

for filename in clean_files:
    if filename.endswith('.json'):
        clean_path = os.path.join(clean_folder, filename)
        raw_path = os.path.join(raw_folder, filename)

        with open(clean_path, 'r', encoding='utf-8') as f:
            clean_data = json.load(f)

        if os.path.exists(raw_path):
            with open(raw_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            clean_data['unprocessed_annotation'] = raw_data['annotation']

            with open(clean_path, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, ensure_ascii=False, indent=4)

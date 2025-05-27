import os
import json

json_folder = 'texts'

redirect_phrase = "Перенаправление на:"

for filename in os.listdir(json_folder):
    if filename.endswith('.json'):
        file_path = os.path.join(json_folder, filename)

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        annotation = data.get("annotation", "")
        if redirect_phrase in annotation:
            os.remove(file_path)
            print(f"Удален файл с перенаправлением: {filename}")
        else:
            print(f"Файл оставлен: {filename}")

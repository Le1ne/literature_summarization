import json
import os
from datasets import load_dataset
from metrics import similarity

SIM_TH = 0.65

with open('filtered_titles_sorted.json', 'r', encoding='utf-8') as f:
    sorted_titles = json.load(f)

annotations_folder = 'processed_annotations'
merged_folder = 'merged_annotations'
os.makedirs(merged_folder, exist_ok=True)

annotations_dict = {}
annotations_files = [file for file in os.listdir(annotations_folder) if file.endswith('.json')]

for file in annotations_files:
    annotation_path = os.path.join(annotations_folder, file)
    try:
        with open(annotation_path, 'r', encoding='utf-8') as af:
            annotation_data = json.load(af)
        title = annotation_data.get("title", "")
        if title in sorted_titles:
            annotations_dict[title] = annotation_data
    except Exception as e:
        print(f"Ошибка при чтении файла {file}: {e}")

# Извлечение исходных текстов из библиотеки librusec для нужных названий
needed_titles = set(annotations_dict.keys())
texts_dict = {}

dataset = load_dataset('IlyaGusev/librusec_full', split='train', streaming=True, trust_remote_code=True)

for record in dataset:
    title = record.get("title", "")
    authors = record.get("authors", [""])
    lang = record.get("lang", "")

    if title in needed_titles:
        if title in texts_dict.keys():
            continue

        if lang not in ['ru', 'rus']:
            continue

        if annotations_dict[title]['author'] in authors:
            texts_dict[title] = record.get("sections", "")
            print(title)
        else:
            for author in authors:
                if similarity(author, annotations_dict[title]['author']) > SIM_TH:
                    texts_dict[title] = record.get("sections", " ")
                    print(title)
                    break

    if len(texts_dict) == len(needed_titles):
        break

# Объединение данных аннотаций с исходными текстами и сохранение в отдельную папку
for file in annotations_files:
    annotation_path = os.path.join(annotations_folder, file)
    try:
        with open(annotation_path, 'r', encoding='utf-8') as af:
            annotation_data = json.load(af)
        title = annotation_data.get("title", "")
        if title in texts_dict:
            annotation_data["text"] = texts_dict[title]
            merged_path = os.path.join(merged_folder, f"{os.path.splitext(file)[0]}.json")
            with open(merged_path, 'w', encoding='utf-8') as mf:
                json.dump(annotation_data, mf, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при обработке файла {file}: {e}")

print("Объединение завершено. Проверьте папку:", merged_folder)

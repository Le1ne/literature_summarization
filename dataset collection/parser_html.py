import os
import json
import re
from bs4 import BeautifulSoup

folder_path = 'raw_pages'
output_folder = 'texts'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def clean_filename(filename):
    # Убираем все символы, которые недопустимы в именах файлов
    return re.sub(r'[\\/*?:"<>|]', "", filename)


# Маркеры для возможного начала пересказа
possible_start_markers = ["Подробный пересказ", "Краткое содержание", "Микропересказ"]

for filename in os.listdir(folder_path):
    if filename.endswith('.raw'):
        file_path = os.path.join(folder_path, filename)

        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        title_tag = soup.find('h1')
        if title_tag:
            title_text = title_tag.get_text().strip()
            match = re.match(r"(.+?)\s*\((.+?)\)", title_text)

            if match:
                title = match.group(1).strip()
                author = match.group(2).strip()
            else:
                title = title_text
                author = ""
        else:
            title = os.path.splitext(filename)[0]
            author = ""

        body_content = soup.find('div', id="bodyContent", class_="bodyContent")

        if body_content:
            raw_text = body_content.get_text(separator="\n").strip()
            end_marker = "Источник"

            start_index = -1
            found_marker = None
            for marker in possible_start_markers:
                start_index = raw_text.find(marker)
                if start_index != -1:
                    found_marker = marker
                    break

            end_index = raw_text.find(end_marker)

            if found_marker and end_index != -1:
                cleaned_text = raw_text[start_index + len(found_marker):end_index].strip()

                cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text).strip()
            elif start_index == -1 and end_index != -1:
                cleaned_text = raw_text[:end_index].strip()
            else:
                cleaned_text = "Не удалось найти текст пересказа."
        else:
            cleaned_text = "Не удалось найти текст пересказа."

        categories_section = soup.find('div', id="catlinks", class_="catlinks")
        if categories_section:
            categories = [cat.get_text().strip() for cat in categories_section.find_all('li')]
        else:
            categories = []

        output_file_path = os.path.join(output_folder, f"{clean_filename(title)}.json")

        data = {
            "title": title,
            "author": author,
            "annotation": cleaned_text,
            "categories": categories,
            "source_file": filename
        }

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        print(f"Данные сохранены в файл: {output_file_path}")

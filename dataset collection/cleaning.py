import json
import os
from utils import oclient


def split_text_into_chunks(text, max_tokens=5000):
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_tokens:
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def clean_annotation(annotation):
    chunks = split_text_into_chunks(annotation, max_tokens=1500)

    print(123)

    cleaned_annotation = ""

    for chunk in chunks:
        # Промпт для модели с целью очистить текст аннотации
        prompt = f"Пожалуйста, очисти следующий текст от служебных данных и символов, оставив только текст пересказа без изменений:\n\n{chunk}\n\nТолько пересказ:"

        # Используем асинхронный запрос к API OpenAI
        res = oclient.chat.completions.create(
            model='qwen2.5-72b',
            messages=[{"role": "user", "content": prompt}],
            temperature=0.01,
            top_p=0.9,
            # logprobs=True,
            # top_logprobs=2,
            extra_body={
                "repetition_penalty": 1.0,
                "guided_choice": None,
                "add_generation_prompt": True,
                "guided_regex": None
            }
        )

        # Обработка ответа
        if res.choices:
            cleaned_annotation += res.choices[0].message.content.strip() + " "
        else:
            print("В ответе нет нужных данных или они пустые.")

    return cleaned_annotation.strip()


json_folder = 'unprocessed_annotations'

for filename in os.listdir(json_folder):
    if filename.endswith('.json'):  # Проверяем, что это JSON файл
        file_path = os.path.join(json_folder, filename)

        # Открытие и чтение содержимого JSON файла
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Проверяем, есть ли ключ 'annotation'
        annotation = data.get("annotation", "")

        if annotation:
            # Очистка аннотации с помощью LLM
            cleaned_annotation = clean_annotation(annotation)

            # Обновляем аннотацию в JSON данных
            data["annotation"] = cleaned_annotation

            # Запись обновленных данных обратно в JSON файл
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)

            print(f"Аннотация очищена и сохранена для файла: {filename}")

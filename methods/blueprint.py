from utils import oclient, client, AsyncList


async def generate_blueprint(model, chunk):
    prompt = f"""Для следующего отрывка текста создайте план, обязательно состоящий из последовательности вопросов и ответов (не более 15 пар, лучше использовать только ключевые вопросы), которые помогут выделить основные события, персонажей и ключевые моменты. Создавайте только план, не добавляя ничего лишнего. Текст:
    ---
    {chunk}
    ---
    Убедитесь, что каждый вопрос обязательно сопровождается четким и кратким ответом."""

    blueprint = await client.get_completion(
        prompt,
        max_tokens=4000,
        rep_penalty=1.0
    )

    print('generated_blueprint')

    return blueprint


async def summarize_with_blueprint(model, chunk, blueprint):
    prompt = f"""Используя следующий план из вопросов и ответов, создайте краткое содержание представленного далее текста:
    ---
    {blueprint}
    ---
    Убедитесь, что текст логически связан и сохраняет важные элементы исходного контекста. Не добавляйте ничего лишнего в ответе.
    Текст:
    {chunk}
    ---"""

    summary = oclient.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.01,
        max_tokens=2000,
        extra_body={
            "repetition_penalty": 1.0,
            "guided_choice": None,
            "add_generation_prompt": True,
            "guided_regex": None
        }
    )

    return summary.choices[0].message.content.strip()


async def text_blueprint_summary(model, chunks, word_limit=500):
    results = AsyncList()

    for chunk in chunks:
        results.append(generate_blueprint(model, chunk))

    await results.complete_couroutines(batch_size=20)
    blueprints = await results.to_list()

    summaries = []

    for chunk, blueprint in zip(chunks, blueprints):
        summaries.append(summarize_with_blueprint(model, chunk, blueprint))

    while len(summaries) > 1:
        merged_level = []
        i = 0

        while i < len(summaries):
            if i + 1 < len(summaries):
                combo = f"{summaries[i]} {summaries[i + 1]}".strip()

                if len(combo.split()) > word_limit:
                    bp = await generate_blueprint(model, combo)
                    combo = await summarize_with_blueprint(model, combo, bp)

                merged_level.append(combo)
                i += 2
            else:
                merged_level.append(summaries[i])
                i += 1

        summaries = merged_level

    final_summary = summaries[0].strip()

    if len(final_summary.split()) > word_limit:
        for _ in range(3):
            bp = await generate_blueprint(model, final_summary)
            final_summary = await summarize_with_blueprint(model, final_summary, bp)

            if len(final_summary.split()) <= word_limit:
                break

    return final_summary

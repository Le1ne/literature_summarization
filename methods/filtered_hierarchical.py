from utils import AsyncList, client, oclient
from metrics import similarity


def filter_near_duplicates(summaries, th: float = .85):
    """сохраняем первую, все следующие сравниваем с последней сохранённой"""
    if not summaries:
        return []

    kept = [summaries[0]]

    for s in summaries[1:]:
        if similarity(s, kept[-1]) < th:
            print('appended')
            kept.append(s)

    return kept


async def summarize_chunk(model, chunk, word_limit=500):
    prompt = f"""
    Ниже приведена часть истории:
    ---
    {chunk}
    ---
    Мы создаем единую всеобъемлющую аннотацию для истории, рекурсивно объединяя фрагменты. Теперь напишите краткое содержание для приведенного выше отрывка, не забудьте включить важную информацию, относящуюся к ключевым событиям, предыстории, обстановке, персонажам, их целям и мотивам. Вы должны кратко представить персонажей, места и другие важные элементы, если они упоминаются в аннотации впервые. История может содержать нелинейные повествования, ретроспективные кадры, переключение между альтернативными мирами или точками зрения и т.д. Поэтому вам следует организовать резюме таким образом, чтобы оно представляло собой последовательное и хронологическое изложение. Несмотря на этот рекурсивный процесс объединения, вам необходимо создать аннотацию, которая будет выглядеть так, как будто она написана на одном дыхании. Аннотация должна состоять из не более {word_limit} слов и может включать несколько абзацев.
    """

    res = await client.get_completion(
        prompt,
        max_tokens=4000,
        rep_penalty=1.0
    )

    print('generated_summ_chunk')

    return res


async def merge_summaries(model, summaries, word_limit=500, use_context=False, previous_summary=''):
    combined_summary = " ".join(summaries)

    if len(combined_summary.split()) > word_limit:
        combined_summary = await summarize_chunk(model, combined_summary, word_limit)

    if use_context:
        prompt = f"""
        Ниже приведено краткое изложение контекста, предшествующего некоторым частям истории:
        ---
        {previous_summary}
        ---
        Ниже приведены несколько кратких изложений последовательных частей рассказа:
        ---
        {combined_summary}
        ---
        Мы создаем единую всеобъемлющую аннотацию для истории, рекурсивно объединяя краткие сведения из ее фрагментов. Теперь объедините предыдущий контекст и краткие содержания в одно краткое содержание, не забудьте включить важную информацию, относящуюся к ключевым событиям, фону, обстановке, персонажам, их целям и мотивам. Вы должны кратко представить персонажей, места и другие важные элементы, если они упоминаются в аннотации впервые. История может содержать нелинейные повествования, ретроспективные кадры, переключение между альтернативными мирами или точками зрения и т.д. Поэтому вам следует организовать аннотацию таким образом, чтобы она представляло собой последовательное и хронологическое изложение. Несмотря на этот рекурсивный процесс объединения, вам необходимо создать аннотацию, которая будет выглядеть так, как будто она написана на одном дыхании. Аннотация должна состоять из {word_limit} слов и может включать несколько абзацев.
        """
    else:
        prompt = f"""
        Ниже приведены несколько кратких изложений последовательных частей рассказа:
        ---
        {combined_summary}
        ---
        Мы последовательно проходим по фрагментам истории, чтобы постепенно обновить общее описание всего сюжета. Напишите краткое содержание для приведенного выше отрывка, не забудьте включить важную информацию, относящуюся к ключевым событиям, предыстории, обстановке, персонажам, их целям и мотивам. Вы должны кратко представить персонажей, места и другие важные элементы, если они упоминаются в аннотации впервые. История может содержать нелинейные повествования, ретроспективные кадры, переключение между альтернативными мирами или точками зрения и т.д. Поэтому вам следует организовать аннотацию таким образом, чтобы она представляла собой последовательное и хронологическое изложение. Несмотря на этот пошаговый процесс обновления аннотации, вам необходимо создать аннотацию, которая будет выглядеть так, как будто она написана на одном дыхании. Аннотация должна содержать примерно {word_limit} слов и может состоять из нескольких абзацев.
        """

    res = oclient.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.01,
        max_tokens=4000,
        extra_body={
            "repetition_penalty": 1.0,
            "guided_choice": None,
            "add_generation_prompt": True,
            "guided_regex": None
        }
    )

    return res.choices[0].message.content.strip()


async def filtered_hierarchical_summary(model, chunks, initial_word_limit=500):
    if not chunks:
        raise ValueError("`chunks` должен содержать хотя бы один элемент!")

    rest_chunks = filter_near_duplicates(chunks)

    results = AsyncList()

    for chunk in rest_chunks:
        results.append(summarize_chunk(model, chunk, initial_word_limit))

    await results.complete_couroutines(batch_size=20)
    summaries = await results.to_list()

    current_level_summaries = summaries
    current_word_limit = initial_word_limit

    if len(current_level_summaries) == 0:
        raise RuntimeError("Не осталось ни одной аннотации после фильтрации узлов!")

    if len(current_level_summaries) == 1:
        return current_level_summaries[0]

    if len(current_level_summaries) == 2:
        return await merge_summaries(model, current_level_summaries, current_word_limit)

    while len(current_level_summaries) > 2:
        next_level_summaries = []
        i = 0

        while i < len(current_level_summaries):
            if i + 2 < len(current_level_summaries):
                temp_summary = await merge_summaries(model, current_level_summaries[i: i + 3], current_word_limit)

                if i + 5 < len(current_level_summaries):
                    temp_summary = await merge_summaries(model, current_level_summaries[i + 3: i + 6], current_word_limit, use_context=True, previous_summary=temp_summary)
                    i += 6
                else:
                    i += 3

                next_level_summaries.append(temp_summary)
            else:
                next_level_summaries.append(current_level_summaries[i])
                i += 1

        current_level_summaries = filter_near_duplicates(next_level_summaries)

    if len(current_level_summaries) == 1:
        return current_level_summaries[0]

    return await merge_summaries(model, current_level_summaries, current_word_limit)

from utils import client, AsyncList


async def generate_pseudo(model, name):
    prompt = f'''Расскажи, пожалуйста, о чём книга "{name}" без текста самой книги.'''

    res = await client.get_completion(
        prompt,
        max_tokens=4000,
        rep_penalty=1.0
    )

    print('generated_pseudo_summ')

    return res


async def pseudo_summaries(model, file_names):
    results = AsyncList()

    for name in file_names:
        results.append(generate_pseudo(model, name))

    await results.complete_couroutines(batch_size=20)
    summaries = await results.to_list()

    summaries_with_names = []

    for name, summ in zip(file_names, summaries):
        summaries_with_names.append((name, summ))

    return summaries_with_names

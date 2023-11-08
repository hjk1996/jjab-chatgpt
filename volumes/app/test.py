


from openai import OpenAI, AsyncClient





openai = OpenAI(
    api_key="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")

text = ""
for chunk in openai.chat.completions.create(
    messages=[
        {"role": "user", "content": "hello. give me the list of the countries of Europe"}
    ],
    model="gpt-3.5-turbo",
    stream=True
    ):
    content = chunk.choices[0].delta.content
    if content is not None:
        text += chunk.choices[0].delta.content 
        print(chunk.choices[0].delta.content)

print(text)
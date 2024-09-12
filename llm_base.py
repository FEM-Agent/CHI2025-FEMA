import time
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key='',
)


def send_message(system_message: str, user_message: str, model='gpt-3.5-turbo'):

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": 'system',
                "content": system_message
            },
            {
                "role": 'user',
                "content": user_message
            }
        ],
        model=model,
    )

    return chat_completion.choices[0].message.content  # , latency  # 返回内容和延迟时间


if __name__ == '__main__':
    system_message = 'this is just a simple test to show the delay of net'
    user_message = 'just test delay'
    for i in range(10000):
        print(send_message(system_message, user_message))

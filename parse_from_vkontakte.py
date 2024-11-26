import time
import requests
V = '5.131'
def get_full_conversation(user_id, access_token):
    offset = 0
    messages = []

    while True:
        response = requests.get('https://api.vk.com/method/messages.getHistory', params={
            'user_id': user_id,
            'count': 200,
            'offset': offset,
            'access_token': access_token,
            'v': V
        }).json()

        if 'response' not in response:
            print("Ошибка:", response)
            break

        items = response['response']['items']
        messages.extend(items)
        offset += 200

        # Остановка, если все сообщения загружены
        if len(items) < 200:
            break

        time.sleep(0.34)  # Ограничение запросов API

    return messages

def get_user_id(username, access_token):
    response = requests.get('https://api.vk.com/method/users.get', params={
        'user_ids': username,
        'access_token': access_token,
        'v': V
    }).json()

    if 'response' in response:
        user_id = response['response'][0]['id']
        return user_id
    else:
        print("Ошибка:", response)
        return None
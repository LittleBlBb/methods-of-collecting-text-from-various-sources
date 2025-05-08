import time
import requests

V = '5.131'  # Версия API ВКонтакте

def get_user_id(username, access_token):
    response = requests.get('https://api.vk.com/method/users.get', params={
        'user_ids': username,
        'access_token': access_token,
        'v': V
    }).json()

    if 'response' in response:
        return response['response'][0]['id']
    else:
        print("Ошибка получения user_id:", response)
        return None

def get_full_conversation(user_id, access_token, update_progress=None):
    offset = 0
    messages = []
    total_messages = None

    while True:
        try:
            response = requests.get('https://api.vk.com/method/messages.getHistory', params={
                'user_id': user_id,
                'count': 200,
                'offset': offset,
                'access_token': access_token,
                'v': V
            }).json()

            if 'response' not in response:
                error = response.get('error', {}).get('error_msg', 'Неизвестная ошибка')
                return None, f"Ошибка API: {error}"

            items = response['response']['items']
            if total_messages is None:
                total_messages = response['response']['count']  # Общее количество сообщений
                if total_messages == 0:
                    return [], "Переписка с пользователем отсутствует или пуста"

            messages.extend(items)
            offset += 200

            if update_progress and total_messages:
                update_progress(len(messages), total_messages)

            if len(items) < 200:
                break

            time.sleep(0.34)  # Ограничение запросов API
        except requests.RequestException as e:
            print(f"Ошибка сети: {e}")
            return None, f"Ошибка сети: {e}"

    return messages, None  # Сообщения и отсутствие ошибки

def get_user_groups(user_id, access_token):
    try:
        response = requests.get('https://api.vk.com/method/groups.get', params={
            'user_id': user_id,
            'access_token': access_token,
            'v': V,
            'extended': 1,
            'fields': 'name'
        }).json()

        if 'response' not in response:
            print(f"Ошибка при получении групп: {response}")
            return []

        groups = response['response']['items']
        return [(group['id'], group['name']) for group in groups]
    except requests.RequestException as e:
        print(f"Ошибка сети: {e}")
        return []

def get_user_posts_in_group_limited(user_id, group_id, access_token, limit=100):
    try:
        response = requests.get('https://api.vk.com/method/wall.get', params={
            'owner_id': f'-{group_id}',
            'count': limit,
            'offset': 0,
            'access_token': access_token,
            'v': V
        }).json()

        if 'response' not in response:
            print(f"Ошибка в группе {group_id}: {response}")
            return []

        items = response['response']['items']
        user_posts = [post for post in items if post.get('from_id') == user_id]
        return user_posts
    except requests.RequestException as e:
        print(f"Ошибка сети: {e}")
        return []

def get_user_posts_in_group_full(user_id, group_id, access_token):
    posts = []
    offset = 0

    while True:
        try:
            response = requests.get('https://api.vk.com/method/wall.get', params={
                'owner_id': f'-{group_id}',
                'count': 100,
                'offset': offset,
                'access_token': access_token,
                'v': V
            }).json()

            if 'response' not in response:
                print(f"Ошибка в группе {group_id}: {response}")
                break

            items = response['response']['items']
            user_posts = [post for post in items if post.get('from_id') == user_id]
            posts.extend(user_posts)
            offset += 100

            if len(items) < 100:
                break

            time.sleep(0.34)
        except requests.RequestException as e:
            print(f"Ошибка сети: {e}")
            break

    return posts

def get_user_posts_in_groups_limited(user_id, access_token, limit_per_group=100, update_progress=None):
    groups = get_user_groups(user_id, access_token)
    all_posts = []

    for i, (group_id, group_name) in enumerate(groups):
        print(f"Собираем последние посты из группы: {group_name}")
        group_posts = get_user_posts_in_group_limited(user_id, group_id, access_token, limit_per_group)
        for post in group_posts:
            post['group_name'] = group_name
        all_posts.extend(group_posts)
        if update_progress:
            update_progress(i + 1, len(groups))

    return all_posts

def get_user_posts_in_groups_full(user_id, access_token, update_progress=None):
    groups = get_user_groups(user_id, access_token)
    all_posts = []

    for i, (group_id, group_name) in enumerate(groups):
        print(f"Собираем все посты из группы: {group_name}")
        group_posts = get_user_posts_in_group_full(user_id, group_id, access_token)
        for post in group_posts:
            post['group_name'] = group_name
        all_posts.extend(group_posts)
        if update_progress:
            update_progress(i + 1, len(groups))

    return all_posts
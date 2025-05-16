import aiohttp
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
V = '5.131'  # Версия API ВКонтакте

class VkApiHandler:
    async def get_user_id(self, username, access_token):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://api.vk.com/method/users.get', params={
                    'user_ids': username,
                    'access_token': access_token,
                    'v': V
                }, ssl=False) as response:
                    data = await response.json()
                    if 'response' in data and data['response']:
                        return data['response'][0]['id']
                    else:
                        error_msg = data.get('error', {}).get('error_msg', 'Неизвестная ошибка')
                        logger.error(f"Ошибка получения user_id: {data}")
                        return None, f"Ошибка API: {error_msg}"
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка сети при получении user_id: {e}")
                return None, f"Ошибка сети: {e}"

    async def get_full_conversation(self, user_id, access_token, update_progress=None):
        offset = 0
        messages = []
        total_messages = None

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get('https://api.vk.com/method/messages.getHistory', params={
                        'user_id': user_id,
                        'count': 200,
                        'offset': offset,
                        'access_token': access_token,
                        'v': V
                    }, ssl=False) as response:
                        data = await response.json()

                        if 'response' not in data:
                            error = data.get('error', {}).get('error_msg', 'Неизвестная ошибка')
                            return None, f"Ошибка API: {error}"

                        items = data['response']['items']
                        if total_messages is None:
                            total_messages = data['response']['count']
                            if total_messages == 0:
                                return [], "Переписка с пользователем отсутствует или пуста"

                        messages.extend(items)
                        offset += 200

                        if update_progress and total_messages:
                            update_progress(len(messages), total_messages)

                        if len(items) < 200:
                            break

                        await asyncio.sleep(0.34)
                except aiohttp.ClientError as e:
                    logger.error(f"Ошибка сети в get_full_conversation: {e}")
                    return None, f"Ошибка сети: {e}"

        return messages, None

    async def get_user_groups(self, user_id, access_token):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.vk.com/method/groups.get', params={
                    'user_id': user_id,
                    'access_token': access_token,
                    'v': V,
                    'extended': 1,
                    'fields': 'name'
                }, ssl=False) as response:
                    data = await response.json()

                    if 'response' not in data:
                        logger.error(f"Ошибка при получении групп: {data}")
                        return []

                    groups = data['response']['items']
                    return [(group['id'], group['name']) for group in groups]
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети в get_user_groups: {e}")
            return []

    async def get_user_posts_in_group_limited(self, user_id, group_id, access_token, limit=100):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.vk.com/method/wall.get', params={
                    'owner_id': f'-{group_id}',
                    'count': limit,
                    'offset': 0,
                    'access_token': access_token,
                    'v': V
                }, ssl=False) as response:
                    data = await response.json()

                    if 'response' not in data:
                        logger.error(f"Ошибка в группе {group_id}: {data}")
                        return []

                    items = data['response']['items']
                    user_posts = [post for post in items if post.get('from_id') == user_id]
                    return user_posts
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети в get_user_posts_in_group_limited: {e}")
            return []

    async def get_user_posts_in_group_full(self, user_id, group_id, access_token):
        posts = []
        offset = 0

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get('https://api.vk.com/method/wall.get', params={
                        'owner_id': f'-{group_id}',
                        'count': 100,
                        'offset': offset,
                        'access_token': access_token,
                        'v': V
                    }, ssl=False) as response:
                        data = await response.json()

                        if 'response' not in data:
                            logger.error(f"Ошибка в группе {group_id}: {data}")
                            break

                        items = data['response']['items']
                        user_posts = [post for post in items if post.get('from_id') == user_id]
                        posts.extend(user_posts)
                        offset += 100

                        if len(items) < 100:
                            break

                        await asyncio.sleep(0.34)
                except aiohttp.ClientError as e:
                    logger.error(f"Ошибка сети в get_user_posts_in_group_full: {e}")
                    break

        return posts

    async def get_user_posts_in_groups_limited(self, user_id, access_token, limit_per_group=100, update_progress=None):
        groups = await self.get_user_groups(user_id, access_token)
        all_posts = []

        for i, (group_id, group_name) in enumerate(groups):
            logger.info(f"Собираем последние посты из группы: {group_name}")
            group_posts = await self.get_user_posts_in_group_limited(user_id, group_id, access_token, limit_per_group)
            for post in group_posts:
                post['group_name'] = group_name
            all_posts.extend(group_posts)
            if update_progress:
                update_progress(i + 1, len(groups))
            await asyncio.sleep(0.34)

        return all_posts

    async def get_user_posts_in_groups_full(self, user_id, access_token, update_progress=None):
        groups = await self.get_user_groups(user_id, access_token)
        all_posts = []

        for i, (group_id, group_name) in enumerate(groups):
            logger.info(f"Собираем все посты из группы: {group_name}")
            group_posts = await self.get_user_posts_in_group_full(user_id, group_id, access_token)
            for post in group_posts:
                post['group_name'] = group_name
            all_posts.extend(group_posts)
            if update_progress:
                update_progress(i + 1, len(groups))
            await asyncio.sleep(0.34)

        return all_posts
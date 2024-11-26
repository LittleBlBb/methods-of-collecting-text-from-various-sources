import json

def extract_texts_from_json(json_data):
    texts = []

    # Проходим по каждому сообщению в JSON-данных
    for message in json_data:
        # Извлекаем основной текст сообщения
        if 'text' in message and message['text']:
            texts.append(message['text'])

        # Извлекаем текст из reply_message, если он существует
        if 'reply_message' in message and 'text' in message['reply_message']:
            texts.append(message['reply_message']['text'])

    return " ".join(texts)  # Объединяем все тексты в одну строку для анализа

def main():
    # Загрузка JSON-файла
    with open('conversation.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # Извлечение и анализ текста
    text = extract_texts_from_json(json_data)
    print(text)
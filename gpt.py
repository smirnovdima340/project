import requests
from transformers import AutoTokenizer
from config import *


class GPT:
    def __init__(self, system_content="Ты - дружелюбный помощник для ответов на вопросы про мошенничество в интернете и фишинг. "
                                      "Давай подробный ответ  на русском языке"):
        self.system_content = system_content
        self.URL = GPT_LOCAL_URL
        self.HEADERS = HEADERS
        self.MAX_TOKENS = MAX_TOKENS
        self.assistant_content = "Ответим на вопрос"

    # Подсчитываем количество токенов в промте
    @staticmethod
    def count_tokens(prompt):
        tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.1")  # название модели
        return len(tokenizer.encode(prompt))

    # Проверка ответа на возможные ошибки и его обработка
    def process_resp(self, response) -> [bool, str]:
        # Проверка статус кода
        if response.status_code != 200:
            return False, f"Ошибка: {response.status_code}"

        # Проверка json
        try:
            full_response = response.json()
        except:
            return False, "Ошибка получения JSON"

        # Проверка сообщения об ошибке
        if "error" in full_response or 'choices' not in full_response:
            return False, f"Ошибка: {full_response}"

        # Результат
        result = full_response['choices'][0]['message']['content']

        # Пустой результат == объяснение закончено
        if result == "":
            return True, "Конец объяснения"

        return True, result

    @staticmethod
    def save_log(user_id, log):
        f = open("log.txt", "w")
        f.write(f"{user_id}: {log}")
        f.close()

    # Формирование промта
    def make_promt(self, user_history):
        json = {
            "messages": [
                {"role": "system", "content": user_history['system_content']},
                {"role": "user", "content": user_history['user_request']},
                {"role": "assistant", "content": user_history['assistant_content']}
            ],
            "temperature": 1.2,
            "max_tokens": self.MAX_TOKENS,
        }
        return json

    # Отправка запроса
    def send_request(self, json):
        resp = requests.post(url=self.URL, headers=self.HEADERS, json=json)
        return resp

    # Сохраняем историю общения
    def save_history(self, assistant_content, content_response):
        return f"{assistant_content} {content_response}"

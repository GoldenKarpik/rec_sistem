import logging
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from deep_translator import GoogleTranslator

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константы для API и настроек
USER_AGENT = 'TravelRecommendationApp/1.0 ()'
OPENTRIPMAP_API_KEY = ''
GEONAMES_USERNAME = ''

# Функция для получения описания из Wikivoyage
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_wikivoyage_description(title: str) -> str:
    try:
        params = {
            'action': 'query',
            'prop': 'extracts',
            'exsectionformat': 'plain',
            'exlimit': '1',
            'titles': title,
            'format': 'json',
            'exintro': False,
            'explaintext': True,
            'exchars': 2000
        }
        headers = {'User-Agent': USER_AGENT}
        response = requests.get('https://en.wikivoyage.org/w/api.php', params=params, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        pages = data['query']['pages']
        page_id = next(iter(pages))
        if page_id != '-1' and 'extract' in pages[page_id]:
            desc = pages[page_id]['extract']
            logging.info(f"Описание для {title} успешно загружено!")
            return desc
        logging.warning(f"Описание для {title} не найдено.")
        return ""
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных для {title}: {str(e)}")
        return ""

# Перевод текста с русского на английский
def translate_to_en(text: str) -> str:
    translator = GoogleTranslator(source='ru', target='en')
    return translator.translate(text)

# Перевод текста с английского на русский
def translate_to_ru(text: str) -> str:
    translator = GoogleTranslator(source='en', target='ru')
    return translator.translate(text)
import json
import os
import logging
from utils import fetch_wikivoyage_description

# Файл для хранения описаний стран
COUNTRY_DESCRIPTIONS_FILE = 'country_descriptions.json'

# Загружаем описания стран из файла или API
def load_country_descriptions(countries: list) -> dict:
    descriptions = {}
    if os.path.exists(COUNTRY_DESCRIPTIONS_FILE):
        try:
            with open(COUNTRY_DESCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                descriptions = json.load(f)
            logging.info(f"Загружено {len(descriptions)} описаний из файла.")
        except Exception as e:
            logging.error(f"Ошибка при чтении файла: {str(e)}")

    # Проверяем каждую страну
    for country in countries:
        country_name = country['Country Name']
        if country_name not in descriptions or not descriptions[country_name]:
            desc = fetch_wikivoyage_description(country_name)
            if desc:
                descriptions[country_name] = desc
            else:
                # Если ничего не нашли, даем базовое описание
                descriptions[country_name] = f"{country_name} - интересное место для путешествий!"

    # Сохраняем обновленные описания
    try:
        with open(COUNTRY_DESCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(descriptions, f, ensure_ascii=False, indent=4)
        logging.info("Описания успешно сохранены!")
    except Exception as e:
        logging.error(f"Ошибка при сохранении: {str(e)}")

    return descriptions
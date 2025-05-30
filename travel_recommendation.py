import logging
import pycountry
from utils import translate_to_en, translate_to_ru, fetch_wikivoyage_description
from models import nlp_model, keyword_extractor, generator
from data_sources import load_country_descriptions
import json
import os
from sentence_transformers import util

# Список стран, которые мы исключаем
EXCLUDED_COUNTRIES = ['Antarctica', 'South Georgia and the South Sandwich Islands']

class TravelRecommendation:
    def __init__(self, user_preferences: str, user_id: str = "default"):
        self.user_preferences = user_preferences
        self.user_id = user_id
        self.fallback_cities = {
            'Nepal': {'name': 'Pokhara', 'lat': 28.2096, 'lon': 83.9856},
            'Switzerland': {'name': 'Zermatt', 'lat': 46.0207, 'lon': 7.7491},
            'El Salvador': {'name': 'San Salvador', 'lat': 13.6929, 'lon': -89.2182},
            'Iceland': {'name': 'Reykjavik', 'lat': 64.1466, 'lon': -21.9426},
            'Mauritania': {'name': 'Nouakchott', 'lat': 18.0735, 'lon': -15.9582},
        }
        self.country_stats = self.get_country_list()
        self.country_descriptions = load_country_descriptions(self.country_stats)
        self.country_embeddings = self.compute_country_embeddings()
        self.user_history = self.load_user_history()

    def get_country_list(self) -> list:
        countries = [
            {'Country Name': country.name, 'Country Code': country.alpha_3}
            for country in pycountry.countries
            if country.name not in EXCLUDED_COUNTRIES
        ]
        logging.info(f"Загружено {len(countries)} стран.")
        return countries

    def load_user_history(self) -> dict:
        history_file = 'user_history.json'
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                logging.info(f"История загружена для {self.user_id}.")
            except Exception as e:
                logging.error(f"Ошибка загрузки истории: {str(e)}")
        return history.get(self.user_id, {'preferred_countries': [], 'past_recommendations': []})

    def save_user_history(self, preferences: dict):
        history_file = 'user_history.json'
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception:
                pass
        history[self.user_id] = preferences
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
            logging.info(f"История сохранена для {self.user_id}.")
        except Exception as e:
            logging.error(f"Ошибка сохранения истории: {str(e)}")

    def compute_country_embeddings(self) -> dict:
        embeddings = {}
        for country, desc in self.country_descriptions.items():
            if desc and country not in EXCLUDED_COUNTRIES:
                embedding = nlp_model.encode(desc, convert_to_tensor=True)
                embeddings[country] = embedding
        logging.info(f"Создано {len(embeddings)} эмбеддингов.")
        return embeddings

    def analyze_preferences(self) -> dict:
        translated = translate_to_en(self.user_preferences)
        keywords = keyword_extractor.extract_keywords(translated, top_n=10)
        keyword_list = [kw[0] for kw in keywords]
        logging.info(f"Ключевые слова: {keyword_list}")
        return {
            "keywords": keyword_list,
            "embedding": nlp_model.encode(translated, convert_to_tensor=True)
        }

    def recommend_countries(self, preferences: dict) -> list:
        user_embedding = preferences['embedding']
        scores = []
        for country, country_embedding in self.country_embeddings.items():
            similarity = float(util.cos_sim(user_embedding, country_embedding))
            scores.append((country, similarity))
        return sorted(scores, key=lambda x: x[1], reverse=True)[:3]

    def generate_recommendations(self) -> str:
        preferences = self.analyze_preferences()
        recommendations = self.recommend_countries(preferences)
        output = "Рекомендации для вашего путешествия:\n\n"

        for idx, (country, score) in enumerate(recommendations, 1):
            # Use country description from country_descriptions.json
            country_desc = self.country_descriptions.get(country, f"{country} is a great destination.")
            # Extract key activities from preferences
            keywords = preferences['keywords'][:5]
            # Generate a structured recommendation
            prompt = (
                f"Create a travel recommendation for {country}. "
                f"Highlight why it matches preferences like {', '.join(keywords)}. "
                f"Include what to see or do, why it’s suitable, and the best time to visit. "
                f"Use this description as context: {country_desc[:500]}..."
            )
            try:
                generated_text = generator(prompt, max_length=200, num_return_sequences=1)[0]['generated_text']
                desc = translate_to_ru(generated_text)
            except Exception as e:
                logging.error(f"Ошибка генерации текста для {country}: {str(e)}")
                desc = f"{country} идеально подходит для ваших предпочтений, таких как {', '.join(keywords)}."

            # Structure the output
            output += f"{idx}. {country} (совпадение: {score:.2f}):\n\n"
            #output += f"**Почему:** {desc[:200]}... Подходит для ваших интересов, таких как {', '.join(keywords)}.\n\n"
            output += f"**Что посмотреть/пройти:**\n"
            # Add city-specific attractions if available
            city = self.fallback_cities.get(country, {}).get('name', 'столица или крупные города')
            output += f"- {city} и окрестности: исследуйте природные достопримечательности и местную культуру.\n"
            output += f"- Активности: треккинг, отдых у костра, знакомство с природой.\n\n"
            output += f"**Почему подходит под запрос:** {country} предлагает уникальные возможности для активного отдыха и релакса на природе, с красивыми пейзажами и атмосферой свободы.\n\n"
            output += f"**Лучшее время:** Май-сентябрь (проверьте погоду для точного планирования).\n"
            output += "-" * 50 + "\n\n"

        self.save_user_history({
            'preferred_countries': preferences['keywords'],
            'past_recommendations': [country for country, _ in recommendations]
        })
        return output
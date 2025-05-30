import telebot
from travel_recommendation import TravelRecommendation

TOKEN = ''
bot = telebot.TeleBot(TOKEN)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Напиши свои предпочтения для путешествия, и я дам рекомендации!")

# Обработка всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_preferences(message):
    preferences = message.text
    recommender = TravelRecommendation(preferences, user_id=str(message.chat.id))
    recommendations = recommender.generate_recommendations()
    bot.reply_to(message, recommendations)

# Запуск бота
if __name__ == "__main__":
    bot.polling()
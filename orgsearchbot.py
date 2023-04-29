# Импортируем необходимые классы.
import requests
import logging
import os
from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN

# Добавим необходимый объект из модуля telegram.ext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove

# клавиатура пользователя с кнопками
reply_keyboard = [['/start', '/stop'], ['/help', '/about']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

# Напишем соответствующие функции.
# Их сигнатура и поведение аналогичны обработчикам текстовых сообщений.


async def start(update, context):
    """Отправляет сообщение когда получена команда /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет! Я бот справочник по организациям. Напишите, что вы ищите? Например, магазин, аптека или школа.",
    )
    # Число-ключ в словаре states —
    # втором параметре ConversationHandler'а.
    return 1
    # Оно указывает, что дальше на сообщения от этого пользователя
    # должен отвечать обработчик states[1].
    # До этого момента обработчиков текстовых сообщений
    # для этого пользователя не существовало,
    # поэтому текстовые сообщения игнорировались.


async def first_response(update, context):
    # Это ответ на первый вопрос.
    # Мы можем использовать его во втором вопросе.
    search_object = update.message.text
    context.user_data['search_object'] = search_object
    await update.message.reply_text(
        "Введите приблизительный адрес (город, улица, дом):")
    # Следующее текстовое сообщение будет обработано
    # обработчиком states[2]
    return 2


async def second_response(update, context):
    # Ответ на второй вопрос.
    # Мы можем его сохранить в базе данных или переслать куда-либо.
    address = update.message.text
    logger.info(address)

    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": address,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if not response:
        # обработка ошибочной ситуации
        pass

    # Преобразуем ответ в json-объект
    json_response = response.json()
    # print(json_response)
    # Получаем первый топоним из ответа геокодера.
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    # Координаты центра топонима:
    toponym_coodrinates = toponym["Point"]["pos"]
    # Долгота и широта:
    toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")

    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

    address_ll = f"{toponym_longitude},{toponym_lattitude}"

    # Справка по параметрам
    # https://yandex.ru/dev/maps/geosearch/doc/concepts/request.html
    search_params = {
        "apikey": api_key,
        "text": context.user_data['search_object'],
        "lang": "ru_RU",
        "ll": address_ll,
        "type": "biz"
    }

    response = requests.get(search_api_server, params=search_params)
    if not response:
        # ...
        pass

    # Преобразуем ответ в json-объект
    json_response = response.json()

    org_list = []

    # Проходим по списку организаций
    for organization in json_response["features"]:
        print(organization)
        # Название организации.
        org_name = organization["properties"]["CompanyMetaData"]["name"]
        # Адрес организации.
        org_address = organization["properties"]["CompanyMetaData"]["address"]
        org_list.append(org_name)
        org_list.append(org_address)
        if "Hours" in organization["properties"]["CompanyMetaData"]:
            org_list.append(
                organization["properties"]["CompanyMetaData"]["Hours"]["text"])
        for phone in organization["properties"]["CompanyMetaData"]["Phones"]:
            org_list.append(phone['formatted'])
        org_list.append('\n')

    # top_list = '\n'.join(org_list[:5])
    top_list = '\n'.join(org_list[:10])
    await update.message.reply_text(f"{top_list}\nЧто ещё поискать?", reply_markup=markup)
    # return ConversationHandler.END  # Константа, означающая конец диалога.
    return 1
    # Все обработчики из states и fallbacks становятся неактивными.


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text("Бот справочник: введите тип организации которую вы ищете, затем приблизительный адрес.")


async def about_command(update, context):
    """Отправляет сообщение когда получена команда /about"""
    await update.message.reply_text("Разработчик: Николай Васин, Санкт-Петербург, 2023г.")


# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)


# Определяем функцию-обработчик сообщений.
# У неё два параметра, updater, принявший сообщение и контекст -
# дополнительная информация о сообщении.
async def echo(update, context):
    # У объекта класса Updater есть поле message,
    # являющееся объектом сообщения.
    # У message есть поле text, содержащее текст полученного сообщения,
    # а также метод reply_text(str),
    # отсылающий ответ пользователю, от которого получено сообщение.
    # await update.message.reply_text('echo: '+ update.message.text,
    # reply_markup=markup)
    await update.message.reply_text('echo: ' + update.message.text)


async def close_keyboard(update, context):
    await update.message.reply_text(
        "OK",
        reply_markup=ReplyKeyboardRemove()
    )


def main():
    # Создаём объект Application.
    # Вместо слова "TOKEN" надо разместить полученный от @BotFather токен
    application = Application.builder().token(BOT_TOKEN).build()

    # Создаём обработчик сообщений ConversationHandler
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)

    # Зарегистрируем их в приложении перед
    # регистрацией обработчика текстовых сообщений.
    # Первым параметром конструктора CommandHandler является название команды.
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()

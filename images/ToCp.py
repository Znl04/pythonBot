import telebot
from datetime import datetime
import openai


class CoffeeBot:
    def __init__(self, token, openai_api_key):
        self.bot = telebot.TeleBot(token)
        self.menu = {
            'Латте': {'300': 750, '400': 900,
                      'description': 'Латте — это скорее молочно-кофейный напиток. Ведь в его основе одна часть эспрессо, целых две или даже три части молока и молочная пенка. Воздушная и в то же время крепкая пенка позволяет создавать узоры на поверхности напитка.'},
            'Капучино': {'300': 730, '400': 880,
                         'description': 'Нежная текстура воздушной молочной пенки в сочетании с ярким ароматом кофе - это и есть причина популярности капучино!'},
            'Эспрессо': {'300': 700, '400': 850,
                         'description': 'Эспрессо – один из основных кофейных напитков, на основе которого созданы десятки самостоятельных рецептов. Эспрессо представляет собой крепкий чёрный кофе с золотистой пенкой, приготовленный в кофемашине.'},
            'Американо': {'300': 820, '400': 920,
                          'description': 'Лунго и американо часто путают, так как оба напитка представляют собой черный кофе с большим объемом воды. Хотя они отличаются по способу приготовления и вкусу.'},
            'Мокачино': {'300': 860, '400': 940,
                         'description': 'Родина моккачино, или мокко, — Америка. Хотя американский напиток очень напоминает итальянский латте. В составе мокко также есть эспрессо, горячее молоко и… шоколад.'},
        }
        self.user_carts = {}
        self.openai_api_key = openai_api_key
        self.start()

    def start(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.bot.send_message(message.chat.id, "Привет! Я бот кофейни. Давайте начнем!")

        @self.bot.message_handler(commands=['menu'])
        def handle_menu(message):
            menu_text = "Меню кофейни:\n"
            for coffee, options in self.menu.items():
                menu_text += f"{coffee} - 300мл: {options['300']} тенге., 400мл: {options['400']} тенге.\n"
            self.bot.send_message(message.chat.id, menu_text)

        @self.bot.message_handler(commands=['aboutcoffee'])
        def handle_about_coffee(message):
            try:
                self.bot.send_message(message.chat.id,
                                      "Введите название кофе или введите /stop чтобы отменить операцию.")
                user_id = message.from_user.id
                if user_id not in self.user_carts:
                    self.user_carts[user_id] = []
                self.user_carts[user_id].append({'state': 'awaiting_coffee_name'})
            except Exception as e:
                print(f"Error in handle_about_coffee: {e}")

        @self.bot.message_handler(func=lambda message: 'state' in self.user_carts.get(message.from_user.id, [])[-1]
        if self.user_carts.get(message.from_user.id) else False)
        def handle_coffee_name(message):
            try:
                entered_coffee_name = message.text.strip().lower()
                matched_coffee = next((coffee for coffee in self.menu if entered_coffee_name in coffee.lower()), None)

                if matched_coffee:
                    prompt = f"Сгенерируйте описание для чашки кофе {matched_coffee}:"
                    coffee_description = self.generate_coffee_description(prompt)

                    coffee_info = f"{matched_coffee} - 300мл: {self.menu[matched_coffee]['300']} тенге., 400мл: {self.menu[matched_coffee]['400']} тенге.\n"
                    coffee_info += f"Описание: {coffee_description}"
                    self.bot.send_message(message.chat.id, coffee_info)
                else:
                    self.bot.send_message(message.chat.id, "Кофе не найден в меню.")
            except Exception as e:
                print(f"Error in handle_coffee_name: {e}")
            finally:
                user_id = message.from_user.id
                if self.user_carts.get(user_id):
                    self.user_carts[user_id][-1]['state'] = ''

        @self.bot.message_handler(commands=['order'])
        def handle_order(message):
            try:
                # Split the command to get the coffee name and volume
                command_parts = message.text.split(' ', 2)
                if len(command_parts) == 3:
                    coffee_name = command_parts[1]
                    volume = command_parts[2]

                    # Check if the provided coffee name is in the menu
                    if coffee_name in self.menu and volume in self.menu[coffee_name]:
                        user_id = message.from_user.id

                        # Initialize user's cart if not exists
                        if user_id not in self.user_carts:
                            self.user_carts[user_id] = []

                        # Add the selected coffee and volume to the user's cart
                        order_item = {'coffee': coffee_name, 'volume': volume}
                        self.user_carts[user_id].append(order_item)

                        self.bot.send_message(message.chat.id, f"Добавлено в корзину: {coffee_name} - {volume}мл")
                    else:
                        self.bot.send_message(message.chat.id, "Кофе или объем не найден в меню.")
                else:
                    self.bot.send_message(message.chat.id, "Используйте команду /order <название кофе> <объем>.")
            except Exception as e:
                print(f"Error in handle_order: {e}")

        @self.bot.message_handler(commands=['cart'])
        def handle_cart(message):
            try:
                user_id = message.from_user.id

                # Check if the user has a cart
                if user_id in self.user_carts and self.user_carts[user_id]:
                    cart_text = "Содержимое вашей корзины:\n"
                    for item in self.user_carts[user_id]:
                        cart_text += f"{item['coffee']} - {item['volume']}мл\n"
                    self.bot.send_message(message.chat.id, cart_text)
                else:
                    self.bot.send_message(message.chat.id, "Ваша корзина пуста.")
            except Exception as e:
                print(f"Error in handle_cart: {e}")

        @self.bot.message_handler(commands=['pay'])
        def handle_pay(message):
            try:
                user_id = message.from_user.id

                # Check if the user has a cart
                if user_id in self.user_carts and self.user_carts[user_id]:
                    total_amount = sum(self.menu[item['coffee']][item['volume']] for item in self.user_carts[user_id])

                    # Simulate a successful payment
                    self.user_carts[user_id] = []  # Clear the user's cart after successful payment

                    # Determine the time of day
                    current_time = datetime.now().time()
                    if current_time < datetime.strptime('12:00:00', '%H:%M:%S').time():
                        greeting = "Доброго утра"
                    elif current_time < datetime.strptime('18:00:00', '%H:%M:%S').time():
                        greeting = "Доброго дня"
                    else:
                        greeting = "хорошего вечера"

                    success_message = f"Оплата успешно произведена. Приятного аппетита и {greeting.lower()}!"
                    self.bot.send_message(message.chat.id, success_message)
                else:
                    self.bot.send_message(message.chat.id, "Ваша корзина пуста.")
            except Exception as e:
                print(f"Error in handle_pay: {e}")

        # Add a message handler to capture user input for payment confirmation
        @self.bot.message_handler(func=lambda message: message.text.isdigit() and int(message.text) > 0)
        def handle_payment_confirmation(message):
            try:
                user_id = message.from_user.id

                # Check if the user is in the payment confirmation state
                if user_id in self.user_carts and self.user_carts[user_id] and self.user_carts[user_id][-1].get(
                        'state') == 'awaiting_payment':
                    entered_amount = int(message.text)
                    total_amount = sum(
                        self.menu[item['coffee']][item['volume']] for item in self.user_carts[user_id][:-1])

                    if entered_amount == total_amount:
                        self.user_carts[user_id] = []  # Clear the user's cart after successful payment

                        # Determine the time of day
                        current_time = datetime.now().time()
                        if current_time < datetime.strptime('12:00:00', '%H:%M:%S').time():
                            greeting = "Доброго утра"
                        elif current_time < datetime.strptime('18:00:00', '%H:%M:%S').time():
                            greeting = "Доброго дня"
                        else:
                            greeting = "хорошего вечера"

                        self.bot.send_message(message.chat.id,
                                              f"Оплата успешно подтверждена. Приятного аппетита и {greeting.lower()}!")
                    else:
                        self.bot.send_message(message.chat.id, "Сумма оплаты не совпадает с общей суммой в корзине.")
                else:
                    self.bot.send_message(message.chat.id, "Ошибка при подтверждении оплаты.")
            except Exception as e:
                print(f"Error in handle_payment_confirmation: {e}")

        @self.bot.message_handler(commands=['info'])
        def handle_info(message):
            info_text = "/start - Начать взаимодействие с ботом\n"
            info_text += "/menu - Показать меню кофейни\n"
            info_text += "/aboutcoffee - Узнать о выбранном кофе\n Введите команду и название кофе!\n"
            info_text += "/order - Заказать кофе\n Введите команду, название кофе и объем.\n"
            info_text += "/cart - Посмотреть содержимое корзины\n"
            info_text += "/pay - Оплатить заказ\n"
            info_text += "/info - Показать информацию о командах"
            self.bot.send_message(message.chat.id, info_text)

    def generate_coffee_description(self, prompt):
        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
            engine="text-davinci-003",  # Используйте актуальное имя модели
            prompt=prompt,
            temperature=0.7,
            max_tokens=150
        )
        return response['choices'][0]['text'].strip()

    def run(self):
        self.start()
        self.bot.polling()


if __name__ == "__main__":
    bot_token = '6690882082:AAEgwRjz1gkwSqhzhr926aQ3SIMVdsDkUuw'
    openai_api_key = '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'
    coffee_bot = CoffeeBot(bot_token, openai_api_key)
    coffee_bot.run()
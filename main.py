from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler
from database.models import User, CarWash, Appointment, Base
from sqlalchemy.sql.expression import extract
#from database.db import Database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)
token = load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_PANEL_PASSWORD = os.getenv('ACCESS_ADMIN_PANEL')
GET_CONTACT = 1
PASSWORD_PROMPT = 2
ADD_CAR_WASH = 3
VIEW_CAR_WASHES = 4
ADD_CAR_WASH_DETAILS = 5
BOOK_CAR_WASH_PROMPT = 6
SELECT_CAR_WASH = 7
SELECT_DATE = 8
SELECT_HOUR = 9
CONFIRM_APPOINTMENT = 10
FINALIZE_APPOINTMENT = 11

engine = create_engine('sqlite:///sqlite_pomoika.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Чтобы пользоваться сервисом пожалуйста поделитесь контактом.', reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Поделиться контактом", request_contact=True)
            ]
        ],
        resize_keyboard=True
    ))
    return GET_CONTACT


def help_command(update: Update, context: CallbackContext) -> None:
    message = update.message if update.message else update.callback_query.message
    #message.reply_text('Все комманды: /start, /add_car_wash, /book_car_wash, /view_my_appointments, /view_my_car_washes')
    query = update.callback_query
    query.message.reply_text("Here is the menu again:", reply_markup=create_menu(context))

def create_menu(context: CallbackContext):
    print('USER_DATA', context.user_data['is_authenticated'])
    if context.user_data['is_authenticated'] == True:
        menu_keyboard = [
            [InlineKeyboardButton("Get help", callback_data='help')],
            [InlineKeyboardButton("Добавить мойку", callback_data='add_car_wash')],
            [InlineKeyboardButton("Забронировать мойку", callback_data='book_car_wash')],
            [InlineKeyboardButton("Мои записи", callback_data='view_my_appointments')],
            [InlineKeyboardButton("Список моек", callback_data='view_my_car_washes')]
        ]
    else:
        menu_keyboard = [
            [InlineKeyboardButton("Get help", callback_data='help')],
            [InlineKeyboardButton("Забронировать мойку", callback_data='book_car_wash')],
            [InlineKeyboardButton("Мои записи", callback_data='view_my_appointments')],
        ]
    return InlineKeyboardMarkup(menu_keyboard)


def menu_actions(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'help':
        help_command(update, context)
    elif query.data == 'add_car_wash':
        add_car_wash_prompt(update, context)
    elif query.data == 'book_car_wash':
        book_car_wash(update, context)
    elif query.data == 'view_my_appointments':
        view_my_appointments(update, context)
    elif query.data == 'view_my_car_washes':
        view_car_washes_prompt(update, context)



def get_contact(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    contact_info = update.message.contact
    if contact_info:

        phone_number = contact_info.phone_number
        context.user_data['phone_number'] = phone_number
        print(context.user_data['phone_number'])
        if context.user_data['phone_number'] == '+77076139019': # AUTH ADMIN USERS
            context.user_data['is_authenticated'] = True
        else:
            context.user_data['is_authenticated'] = False
        first_name = contact_info.first_name
        last_name = contact_info.last_name or "N/A"
    
        update.message.reply_text(
                    "Welcome!",
                    reply_markup=create_menu(context)  # Display the menu here
                )

        session = Session()
        # Check if the user already exists in the database
        user = session.query(User).filter_by(phone_number=phone_number).first()
        if user:
            update.message.reply_text(
            "Welcome back!\n\n"
            # "Все комманды:\n\n"
            # "/help - get help\n"
            # "/add_car_wash - Добавить мойку\n"
            # "/book_car_wash - Забронировать мойку\n"
            # "/view_my_appointments - Мои записи\n"
            # "/view_my_car_washes - Список моек\n"
        )
            session.close()
            return ConversationHandler.END

        new_user = User(phone_number=phone_number, name=first_name, last_name=last_name)
        session.add(new_user)
        session.commit()
        session.close()

        update.message.reply_text(
            "Все комманды:\n\n"
            # "/help - get help\n"
            # "/add_car_wash - Добавить мойку\n"
            # "/book_car_wash - Забронировать мойку\n"
            # "/view_my_appointments - Мои записи\n"
            # "/view_my_car_washes - Список моек\n"
        )
        return ConversationHandler.END
    else:
        update.message.reply_text("Please share your contact to continue.")
        return GET_CONTACT
    
    # update.message.reply_text("Choose an option:", reply_markup=create_menu())
    #     return ConversationHandler.END

def check_password(update: Update, context: CallbackContext) -> int:
    context.user_data['command'] = update.message.text.split()[0][1:] # Save the command without the leading '/'
    update.message.reply_text('Введите секретный пароль:')
    return PASSWORD_PROMPT


def handle_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text
    command = context.user_data['command']
    print(f"Received password: {password}, Expected password: {ADMIN_PANEL_PASSWORD}")
    if password == ADMIN_PANEL_PASSWORD:
        print(f"Command: {command}")
        if command == 'add_car_wash':
            return ask_for_details(update, context)
        elif command == 'view_my_car_washes':
            return VIEW_CAR_WASHES
    else:
        update.message.reply_text('Неправильный пароль.')
        return ConversationHandler.END


def ask_for_details(update: Update, context: CallbackContext) -> int:
    context.user_data['details_stage'] = 1
    update.message.reply_text('Напишите имя автомойки:')
    return ADD_CAR_WASH_DETAILS


def collect_details(update: Update, context: CallbackContext) -> int:
    #update.callback_query.message.text
    text = update.callback_query.message.text
    stage = context.user_data.get('details_stage', 1)
    print('STAGE', stage)

    if stage == 1:
        context.user_data['name'] = text
        update.message.reply_text('Спасибо! Напишите контактный номер телефона:')
    elif stage == 2:
        context.user_data['contact_phone_number'] = text
        update.message.reply_text('Отлично! Теперь, напишите доступные часы для пользования (прим. "11,12,1,2,3"):')
    elif stage == 3:
        context.user_data['available_hours'] = text.replace(' ', '') # Remove spaces
        update.message.reply_text('Почти готово! Вставьте ссылку 2GIS для вашей мойки:')
    elif stage == 4:
        context.user_data['link_2gis'] = text
        update.message.reply_text('Последнее, напишите цену за одну мойку:')
    elif stage == 5:
        context.user_data['price'] = text
        session = Session()
        new_car_wash = CarWash(
            name=context.user_data['name'],
            contact_phone_number=context.user_data['contact_phone_number'],
            available_hours=context.user_data['available_hours'],
            link_2gis=context.user_data['link_2gis'],
            price=context.user_data['price']
        )
        session.add(new_car_wash)
        session.commit()
        session.close()
        update.message.reply_text('Автомойка добавлена успешно!')
        return ConversationHandler.END

    context.user_data['details_stage'] += 1
    return ADD_CAR_WASH_DETAILS


def book_car_wash(update: Update, context: CallbackContext) -> int:
    return book_car_wash_prompt(update, context)


def add_car_wash_prompt(update: Update, context: CallbackContext) -> int:
    # Retrieve the car wash details from context.user_data
    name = context.user_data.get('name')
    contact_phone_number = context.user_data.get('contact_phone_number')
    print('PARSED NAME IS ', name)
    available_hours = context.user_data.get('available_hours')
    link_2gis = context.user_data.get('link_2gis')
    price = context.user_data.get('price')
    message = update.message if update.message else update.callback_query.message

    # Check if the necessary details are provided
    if name and contact_phone_number and available_hours and link_2gis and price:
        session = Session()
        
        # Create a new CarWash instance with the provided details
        new_car_wash = CarWash(
            name=name,
            contact_phone_number=contact_phone_number,
            available_hours=available_hours,
            link_2gis=link_2gis,
            price=price
        )
        
        # Add the new CarWash to the session and commit it to the database
        session.add(new_car_wash)
        session.commit()
        session.close()

        message.reply_text('Автомойка добавлена успешно!')
    else:
        message.reply_text('Не удалось добавить мойку. Предоставьте полную информацию.')
    
    query = update.callback_query
    query.message.reply_text("Here is the menu again:", reply_markup=create_menu(context))
    return ConversationHandler.END


#BOOK CAR WASH
def book_car_wash_prompt(update: Update, context: CallbackContext) -> int:
    
    message = update.message if update.message else update.callback_query.message

    logging.debug(update)
    session = Session()
    car_washes = session.query(CarWash).all()

    session.close()

    car_washes_list = "\n".join([f"{i}: {car_wash.name}, Contact: {car_wash.contact_phone_number}, Price: {car_wash.price}" for i, car_wash in enumerate(car_washes)])
    
    if car_washes_list:
        message.reply_text('Напишите число чтобы выбрать автомойку:\n' + car_washes_list)
    else:
        message.reply_text('Автомойки не найдены.')
        return ConversationHandler.END

    context.user_data['car_washes'] = car_washes  # Save the car washes to the context
    return SELECT_CAR_WASH


def select_car_wash(update: Update, context: CallbackContext) -> int:
    selected_index = int(update.message.text)
    selected_car_wash = context.user_data['car_washes'][selected_index - 1]  # Indexing from 1
    
    context.user_data['selected_car_wash'] = selected_car_wash
    hours = selected_car_wash.available_hours.split(",")

    update.message.reply_text(f"Вы выбрали - {selected_car_wash.name}. Напишите дату записи (e.g., 2023-08-07):")
    return SELECT_DATE


def select_date(update: Update, context: CallbackContext) -> int:
    selected_date = update.message.text
    context.user_data['selected_date'] = selected_date
    selected_car_wash = context.user_data['selected_car_wash']
    hours = selected_car_wash.available_hours.split(",")  
    available_hours = [int(hour) for hour in hours]

    # Checking existing appointments for that car wash and date
    session = Session()
    existing_appointments = session.query(Appointment).filter(
        Appointment.car_wash_id == selected_car_wash.id,
        extract('year', Appointment.start_date) == int(selected_date.split("-")[0]),
        extract('month', Appointment.start_date) == int(selected_date.split("-")[1]),
        extract('day', Appointment.start_date) == int(selected_date.split("-")[2])
    ).all()
    session.close()

    taken_hours = [appointment.start_date.hour for appointment in existing_appointments]
    for hour in taken_hours:
        if hour in available_hours:
            available_hours.remove(hour)

    if available_hours:
        context.user_data['available_hours'] = available_hours  # Save available hours in context
        update.message.reply_text(f"Available hours for {selected_date} are: {', '.join(map(str, available_hours))}. Please select one.")
        return SELECT_HOUR
    else:
        update.message.reply_text(f"No available hours for {selected_date}. Please select a different date.")
        return SELECT_DATE  # Looping back to the date selection


def select_hour(update: Update, context: CallbackContext) -> int:
    selected_hour = int(update.message.text)
    selected_date = context.user_data['selected_date']
    selected_car_wash = context.user_data['selected_car_wash']
    user_phone_number = context.user_data['phone_number']
    # Create an appointment
    session = Session()
    new_appointment = Appointment(
        user_phone_number=user_phone_number,
        car_wash_id=selected_car_wash.id,
        start_date=datetime.strptime(selected_date + " " + str(selected_hour), "%Y-%m-%d %H"),
        end_date=datetime.strptime(selected_date + " " + str(selected_hour), "%Y-%m-%d %H"),
        status="booked",
        price=selected_car_wash.price
    )
    session.add(new_appointment)
    session.commit()
    session.close()

    update.message.reply_text(f"Appointment booked for {selected_date} at {selected_hour}.")
    return ConversationHandler.END


def confirm_appointment(update: Update, context: CallbackContext) -> int:
    selected_car_wash = context.user_data['selected_car_wash']
    selected_date = context.user_data['selected_date']
    selected_hour = context.user_data['selected_hour']

    update.message.reply_text(
        f"You've selected {selected_car_wash.name} on {selected_date} at {selected_hour}:00. "
        "Type 'confirm' to finalize your booking or 'cancel' to abort."
    )
    return FINALIZE_APPOINTMENT


def finalize_appointment(update: Update, context: CallbackContext) -> int:
    user_response = update.message.text.lower()
    if user_response == 'confirm':
        # Here you'd add the appointment to your database
        update.message.reply_text("Your appointment has been booked!")
        query = update.callback_query
        query.message.reply_text("Here is the menu again:", reply_markup=create_menu(context))
        return ConversationHandler.END
    elif user_response == 'cancel':
        update.message.reply_text("Your appointment has been cancelled.")
        query = update.callback_query
        query.message.reply_text("Here is the menu again:", reply_markup=create_menu(context))
        return ConversationHandler.END
    else:
        update.message.reply_text("Please type 'confirm' to finalize your booking or 'cancel' to abort.")
        return CONFIRM_APPOINTMENT  # Send them back to the confirmation stage


def view_my_appointments(update: Update, context: CallbackContext) -> None:
    # Assuming phone_number is available from user contact
    #print(context.user)
    phone_number = context.user_data['phone_number']
    message = update.message if update.message else update.callback_query.message
    session = Session()
    user = session.query(User).filter_by(phone_number=phone_number).first()

    if user:
        appointments = user.appointments  # Assuming 'appointments' is a relationship attribute in the User class
        if appointments:
            response_text = "Ваши записи:\n"
            for appointment in appointments:
                response_text += f"Car Wash: {appointment.car_wash.name}, Date: {appointment.start_date}\n"
            message.reply_text(response_text)
        else:
            message.reply_text('У вас нет записей.')
    else:
        message.reply_text('Не удалось найти ваш номер телефона в базе данных.')

    session.close()

    
def view_car_washes_prompt(update: Update, _: CallbackContext) -> int:
    
    message = update.message if update.message else update.callback_query.message

    session = Session()
    car_washes = session.query(CarWash).all()
    session.close()
    
    car_washes_list = "\n".join([
        f"Название: {car_wash.name}, Телефон: {car_wash.contact_phone_number}, \
        Цена: {car_wash.price}" for car_wash in car_washes
    ])
    
    if car_washes_list:
        message.reply_text('Список автомоек:\n' + car_washes_list)
    else:
        message.reply_text('Автомойки не найдены.')
    
    query = update.callback_query
    query.message.reply_text("Here is the menu again:", reply_markup=create_menu())
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('start', start),
        CommandHandler('add_car_wash', check_password),
        CommandHandler('view_my_car_washes', check_password),
        CommandHandler('book_car_wash', book_car_wash_prompt)
    ],
    states={
        GET_CONTACT: [MessageHandler(Filters.contact, get_contact)],
        PASSWORD_PROMPT: [MessageHandler(Filters.text, handle_password)],
        ADD_CAR_WASH_DETAILS: [MessageHandler(Filters.text, collect_details)],
        ADD_CAR_WASH: [MessageHandler(Filters.text, ask_for_details)],  # Add this line
        VIEW_CAR_WASHES: [MessageHandler(Filters.text, view_car_washes_prompt)],
        BOOK_CAR_WASH_PROMPT: [MessageHandler(Filters.text, book_car_wash_prompt)],
        SELECT_CAR_WASH: [MessageHandler(Filters.text, select_car_wash)],
        SELECT_DATE: [MessageHandler(Filters.text, select_date)],
        SELECT_HOUR: [MessageHandler(Filters.text, select_hour)],
        CONFIRM_APPOINTMENT: [MessageHandler(Filters.text, confirm_appointment)],
        FINALIZE_APPOINTMENT: [MessageHandler(Filters.text, finalize_appointment)]
    },
    fallbacks=[CommandHandler('cancel', lambda update, context: ConversationHandler.END)],
)

def main() -> None:

    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(menu_actions))
    dp.add_handler(CommandHandler("add_car_wash", check_password))
    dp.add_handler(CommandHandler("book_car_wash", book_car_wash))
    dp.add_handler(CommandHandler("view_my_appointments", view_my_appointments))
    dp.add_handler(CommandHandler("view_my_car_washes", check_password))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()



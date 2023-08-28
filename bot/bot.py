from telegram.ext import Updater
from handlers import admin, client, owner
from telegram.ext import CommandHandler

class Bot:
    def __init__(self, token):
        self.updater = Updater(token=token, use_context=True)

        self.updater.dispatcher.add_handler(CommandHandler("start", self.start))

        # Client commands
        # self.updater.dispatcher.add_handler(
        #     CommandHandler("findcarwash", client.find_carwash))
        # self.updater.dispatcher.add_handler(
        #     CommandHandler("schedule", client.schedule))

        # # Owner commands
        # self.updater.dispatcher.add_handler(
        #     CommandHandler("addcarwash", owner.add_carwash))

        # # Admin commands
        # self.updater.dispatcher.add_handler(
        #     CommandHandler("viewusers", admin.view_users))
        # self.updater.dispatcher.add_handler(
        #     CommandHandler("viewcarwashes", admin.view_carwashes))
        # self.updater.dispatcher.add_handler(CommandHandler(
        #     "viewappointments", admin.view_appointments))

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

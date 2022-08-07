import logging
from telegram.ext.filters import Filters
from numpy import number
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.ext.callbackcontext import CallbackContext
from telegram import (ChatAction)
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, KeyboardButton
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from urllib import response
from urllib.request import urlopen
from telegram import BotCommand
import re
import requests
import json
import os
import time
import hashlib

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# API KEY of Telegram Bot
TOKEN = '1240382:XXxxxxxxxxxxxxxxxxxxxxxxx'


# Function verify phone and generate OTP
def validatePhone(ph):
    # Counting length of the number
    if len(str(ph)) == 10:
        # Converting integer to string
        tx = str(ph)
        # Check if input is number
        # Number start with 9,8,7 or 6 only 10 digit
        res = bool(re.match(r'^(9|8|7|6)[0-9]{9}$', tx))
        if res == True:
            num_headers = {'accept': 'application/json', }
            num_json_data = {'mobile': ph}
            num_response = requests.post(
                'https://cdn-api.co-vin.in/api/v2/auth/public/generateOTP', headers=num_headers, json=num_json_data)
            num_responseCode = num_response.status_code
            if num_responseCode == 200:
                num_responseCode = num_response.status_code
                num_txnId_data = num_response.text
                num_txnId = json.loads(num_txnId_data)
                txn = (num_txnId["txnId"])
                # Transaction id generated and returned
                return [True, txn]
            elif num_responseCode == 500:
                return [False, "Server busy, please try after sometime"]
            elif num_responseCode == 400:
                return [False, "Please try again after sometime"]
            elif num_responseCode == 401:
                return [False, "Unauthorized!"]
            else:
                return [False, "Unknown error occured!"]

        else:
            return [False, "Please enter a valid phone number."]
    else:
        return [False, "Please enter a valid phone number."]


# Function verify OTP, Error will be return if no beneficiary id linked to number
def validateOTP(ph, txn):
    if len(str(ph)) == 6:
        tx = str(ph)
        res = bool(re.match(r'^[0-9]{6}$', tx))
        if res == True:
            bOTP = bytes(str(ph), encoding='utf-8')
            # Converting OTP to sha256 hash
            otp_hashed = hashlib.sha256(bOTP).hexdigest()
            otp_headers = {'accept': 'application/json', }
            otp_json_data = {'otp': otp_hashed,
                             'txnId': txn}
            otp_response = requests.post(
                'https://cdn-api.co-vin.in/api/v2/auth/public/confirmOTP', headers=otp_headers, json=otp_json_data)
            otp_responseCode = otp_response.status_code
            if otp_responseCode == 200:
                otp_txnId_data = otp_response.text
                otp_txnId = json.loads(otp_txnId_data)
                otp_token = otp_txnId["token"]
                # Download token has been returned
                return [True, otp_token]
            elif otp_responseCode == 500:
                return [False, "Server busy, please try after sometime"]
            elif otp_responseCode == 400:
                return [False, "Please try again after sometime"]
            elif otp_responseCode == 401:
                return [False, "Unauthorized!"]
            else:
                return [False, "Unknown error occured!"]

        else:
            return [False, "Invalid OTP."]
    else:
        return [False, "Invalid OTP."]

# Function verify Beneficiary ID


def validateBID(ph, token):
    if len(str(ph)) == 14:
        tx = str(ph)
        res = bool(re.match(r'^[0-9]{14}$', tx))
        if res == True:
            dl_authToken = 'Bearer ' + token
            dl_headers = {'accept': 'application/pdf',
                          'Authorization': dl_authToken, }
            dl_params = {'beneficiary_reference_id': ph, }
            dl_response = requests.get(
                'https://cdn-api.co-vin.in/api/v2/registration/certificate/public/download', params=dl_params, headers=dl_headers)
            dl_responseCode = dl_response.status_code
            if dl_responseCode == 200:
                fname = 'certificate-'+tx+'.txt'
                with open(fname, 'wb') as f:
                    f.write(dl_response.content)
                # Downloaded content and saved temporary as text file and return file name
                return [True, fname]
            elif dl_responseCode == 500:
                return [False, "Beneficiary ID does not exists."]
            elif dl_responseCode == 400:
                return [False, "Please try again after sometime"]
            elif dl_responseCode == 401:
                return [False, "Unauthorized!"]
            else:
                return [False, "Unknown error occured!"]
        else:
            return [False, "Invalid Beneficiary ID."]
    else:
        return [False, "Invalid Beneficiary ID."]


# Start function of bot
def start(update: Update, context: CallbackContext):
    # Button trigger conversation handler
    buttons = [[KeyboardButton("Download Certificate")]]
    context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    msg = "Hi {}, \nI'm {}.\nI can help you to download your Covid-19 vaccine certificate.\n\n<u><b>Step to download certificate:</b></u>\n\n1.Click on 'Download Certificate' button.\n\n2.Enter your phone number.\n\n3.Enter OTP you received within 3 minutes.\n\n4.Now enter your Beneficiary ID to confirm download.\n\nBot can't store your file, so it will deleted automatically from it's server.".format(
        update.message.from_user.full_name, context.bot.name)
    context.bot.send_message(
        chat_id=update.effective_message.chat_id, text=msg, parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))


# Conversation ask phone number
def askPhone(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("Cancel")]]
    context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    context.bot.send_message(chat_id=update.message.from_user.id, text="Enter your phone number.",
                             parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return PHONE


# Conversation processing phone number
def phone(update: Update, context: CallbackContext):
    isPhone = validatePhone(update.message.text)
    if isPhone[0] == True:
        context.user_data["txnId"] = isPhone[1]
        msg = "Enter the OTP received on phone +91{}".format(
            update.message.text)
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text=msg,
                                 parse_mode="HTML")
        return OTP
    else:
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text=isPhone[1],
                                 parse_mode="HTML")
        return PHONE

# Conversation processing OTP


def otp(update: Update, context: CallbackContext):
    isOTP = validateOTP(update.message.text, context.user_data["txnId"])
    if isOTP[0] == True:
        context.user_data["token"] = isOTP[1]
        msg = "Enter your 14 digit Beneficiary ID."
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text=msg,
                                 parse_mode="HTML")
        return BID
    else:
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text=isOTP[1],
                                 parse_mode="HTML")
        return OTP

# Conversation processing Beneficiary ID


def bid(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton("Cancel")]]
    isBID = validateBID(update.message.text, context.user_data["token"])
    if isBID[0] == True:
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text="Sending file...",
                                 parse_mode="HTML")
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        context.bot.send_document(update.message.chat.id, document=open(
            isBID[1], 'rb'), filename="certificate.pdf")
        os.remove(isBID[1])
        time.sleep(1)
        buttons = [[KeyboardButton("Download Certificate")]]
        context.bot.send_message(chat_id=update.effective_message.chat_id,
                                 text="Download completed.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        return ConversationHandler.END
    else:
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        context.bot.send_message(chat_id=update.message.from_user.id, text=isBID[1],
                                 parse_mode="HTML")
        return BID


def help(update: Update, context: CallbackContext):
    yourname = update.message.from_user.full_name

    msg = "Hi {}\n\nWelcome to Covid vaccine certificate downloader bot 🤖.\n\n✅1.To download certificate you must have your 14 didgit cowin Beneficiary ID.\n\n✅2.Enter your mobile number.\n\n✅3.You will receive an OTP if you have given correct number.\n\n✅4.Then enter the OTP.\n\n✅5.After that enter your 14 digit, Beneficiary ID.\n\n✅6.Use command /cancel to cancel download process.\n\n<i>OTP is only valid for 3 minutes, so session expires quickly.</i>".format(
        yourname)
    context.bot.send_message(update.message.chat.id, msg)


def cancel(update: Update, context: CallbackContext):
    bot = context.bot
    buttons = [[KeyboardButton("Download Certificate")]]
    bot.send_message(chat_id=update.effective_message.chat_id,
                     text="Download process has been cancelled by user.", parse_mode="HTML", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return ConversationHandler.END


PHONE, OTP, BID = range(3)


def main():
    # to get the updates from bot
    updater = Updater(token=TOKEN, use_context=True)

    # to dispatch the updates to respective handlers
    dp = updater.dispatcher

    # handlers
    dp.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(
            "^(Download Certificate)$"), askPhone)],
        states={
            PHONE: [MessageHandler(~Filters.command, phone)],
            OTP: [MessageHandler(~Filters.command, otp)],
            BID: [MessageHandler(~Filters.command, bid)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    dp.add_handler(MessageHandler(Filters.regex("^(cancel|Cancel)$"), cancel))
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


# start application with main function
if __name__ == '__main__':
    main()

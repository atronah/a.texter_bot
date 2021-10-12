#! /usr/bin/env python3

import pytesseract
from pdf2image import convert_from_path
from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

TOKEN = 


def start(update: Update, context: CallbackContext):
    update.message.reply_text('Hello. Send me your pdf')


def process_attachment(update: Update, context: CallbackContext):
    attachment = update.message.document

    downloaded_path = context.bot.getFile(attachment).download()

    page_content = []
    pdf_pages = convert_from_path(downloaded_path, 100)
    for page in pdf_pages:
        page_content.append(str(pytesseract.image_to_string(page, 'rus')))

    content = '\n'.join(page_content)
    update.message.reply_text(f'file_id={attachment.file_id}, downloaded_path={downloaded_path}\n'
                              f'Content:\n'
                              f'{content}')


updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.attachment, process_attachment))

updater.start_polling()
updater.idle()

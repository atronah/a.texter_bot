#! /usr/bin/env python3

import os
import collections
import logging
import logging.config
import yaml
from typing import Dict, Any


import pytesseract
from pdf2image import convert_from_path

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

settings: Dict[str, Dict[str, Any]] = {
    'access': {
        'token': None,
        'user_list': []
    },
    'logging': {
        'version': 1.0,
        'formatters': {
            'default': {
                'format': '[{asctime}]{levelname: <5}({name}): {message}',
                'style': '{'
            }
        },
        'handlers': {
            'general': {
                'class': 'logging.handlers.WatchedFileHandler',
                'level': 'INFO',
                'filename': 'bot.log',
                'formatter': 'default'
            },
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default'
            },
            'unknown_messages': {
                'class': 'logging.handlers.WatchedFileHandler',
                'level': 'INFO',
                'filename': 'unknown_messages.log',
                'formatter': 'default'
            }
        },
        'loggers': {
            'unknown_messages': {
                'level': 'INFO',
                'handlers': ['unknown_messages']
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['general']
        },
    }
}


def recursive_update(target_dict, update_dict):
    if not isinstance(update_dict, dict):
        return target_dict
    for k, v in update_dict.items():
        if isinstance(v, collections.abc.Mapping):
            target_dict[k] = recursive_update(target_dict.get(k, {}), v)
        else:
            target_dict[k] = v
    return target_dict


if os.path.exists('conf.yaml'):
    with open('conf.yaml', 'rt') as conf:
        recursive_update(settings, yaml.safe_load(conf))
else:
    with open('conf.yml', 'wt') as conf:
        yaml.dump(settings, conf)


logging.config.dictConfig(settings['logging'])


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in settings['access']['user_list']:
        update.message.reply_text(f'Your user ID is {user_id}')
        other_messages(update, context)
    else:
        update.message.reply_text('Hello. Send me your pdf')


def process_attachment(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in settings['access']['user_list']:
        update.message.reply_text(f'Your user ID is {user_id}')
        other_messages(update, context)
    else:
        attachment = update.message.document

        downloaded_path = context.bot.getFile(attachment).download()

        page_content = []
        pdf_pages = convert_from_path(downloaded_path, 100)
        LENGTH_LIMIT = 4000
        for idx, page in enumerate(pdf_pages):
            page_content = str(pytesseract.image_to_string(page, 'rus'))
            for part in [page_content[i:i+LENGTH_LIMIT] for i in range(0, len(page_content), LENGTH_LIMIT)]:
                update.message.reply_text(f'Page {idx+1}\n\n{part}')


def error_handler(update: Update, context: CallbackContext):
    exception_info = str(context.error)
    # import traceback
    # exception_info += os.linesep
    # exception_info += traceback.format_exc()
    context.bot.sendMessage(update.effective_chat.id, f'Internal exception: {exception_info}')
    raise context.error


def other_messages(update: Update, context: CallbackContext):
    logger = logging.getLogger('unknown_messages')
    logger.info(f'{update.effective_user.id} {update.message.text}')
    update.message.reply_text("Unsupported or unauthorized. Logged.")


updater = Updater(token=settings['access']['token'], use_context=True)
dispatcher = updater.dispatcher


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.attachment, process_attachment))
dispatcher.add_error_handler(error_handler)
dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.attachment & ~Filters.status_update, other_messages))

updater.start_polling()
updater.idle()

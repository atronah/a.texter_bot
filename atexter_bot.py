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
    'bot': {
        'token': None
    },
    'tesseract': {
        'cmd': None
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

access = {
    'admins': {},
    'users': {},
    'unknown': {},
    'rejected': {},
}


def has_access(user_id):
    if user_id in access['admins'] or user_id in access['users']:
        return True
    return False


def is_admin(user_id):
    if user_id in access['admins']:
        return True
    return False


def remove_user(user_id, list_name='users'):
    while user_id in access[list_name]:
        del access[list_name][user_id]


def add_user(user_id, username, list_name='users'):
    if user_id not in access[list_name]:
        access[list_name][user_id] = username
        if list_name == 'rejected':
            remove_user(user_id, 'users')
        elif list_name in ('admin', 'users'):
            remove_user(user_id, 'unknown')
            remove_user(user_id, 'rejected')
        save('access.yaml', access)
        return True
    return False


def recursive_update(target_dict, update_dict):
    if not isinstance(update_dict, dict):
        return target_dict
    for k, v in update_dict.items():
        if isinstance(v, collections.abc.Mapping):
            target_dict[k] = recursive_update(target_dict.get(k, {}), v)
        else:
            target_dict[k] = v
    return target_dict


def load(filename, data):
    if os.path.exists(filename):
        with open(filename, 'rt') as conf:
            recursive_update(data, yaml.safe_load(conf))
        return True
    return False


def save(filename, data):
    with open(filename, 'wt') as conf:
        yaml.dump(data, conf)


if not load('conf.yaml', settings):
    save('conf.yaml', settings)
    
if not load('access.yaml', access):
    save('access.yaml', access)


if settings['tesseract']['cmd']:
    pytesseract.pytesseract.tesseract_cmd = settings['tesseract']['cmd']

logging.config.dictConfig(settings['logging'])


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in access['users']:
        update.message.reply_text(f'Your user ID is {user_id}')
        other_messages(update, context)
    else:
        update.message.reply_text('Hello. Send me your pdf')


def process_attachment(update: Update, context: CallbackContext):
    user = update.effective_user
    if has_access(user.id):
        attachment = update.message.document

        downloaded_path = context.bot.getFile(attachment).download()

        pdf_pages = convert_from_path(downloaded_path, 100)
        LENGTH_LIMIT = 4000
        for page_idx, page in enumerate(pdf_pages):
            page_content = str(pytesseract.image_to_string(page, 'rus'))
            for part_idx, part in enumerate([page_content[i:i+LENGTH_LIMIT]
                                             for i in range(0, len(page_content), LENGTH_LIMIT)]):
                if part.strip() > '':
                    update.message.reply_text(f'Page {page_idx + 1} part {part_idx + 1} \n\n'
                                              f'{part.strip()}')

        os.remove(downloaded_path)
    else:
        update.message.reply_text(f'Your user ID is {user.id}')
        add_user(user.id, f'{user.username} ({user.name}, {user.full_name})', 'unknown')
        other_messages(update, context)


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


def unknown_list(update: Update, context: CallbackContext):
    if is_admin(update.effective_user.id):
        if access['unknown']:
            update.message.reply_text('\n'.join([f'{k}: {v}' for k, v in access['unknown'].items()]))
        else:
            update.message.reply_text('No unknowns')
    else:
        update.message.reply_text("You're not an admin")


def accept(update: Update, context: CallbackContext):
    if is_admin(update.effective_user.id):
        for user_id in map(int, context.args):
            username = access['unknown'].get(user_id) or access['rejected'].get(user_id)
            if add_user(user_id, username, 'users'):
                update.message.reply_text(f'User {user_id} has been added to user list')
            elif user_id in access['users']:
                update.message.reply_text(f'User {user_id} is already in the user list')
            else:
                update.message.reply_text(f'Unknown problem')
    else:
        update.message.reply_text("You're not an admin")


updater = Updater(token=settings['bot']['token'], use_context=True)
dispatcher = updater.dispatcher


dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('unknown_list', unknown_list))
dispatcher.add_handler(CommandHandler('accept', accept))
dispatcher.add_handler(MessageHandler(Filters.attachment, process_attachment))
dispatcher.add_error_handler(error_handler)
dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.attachment & ~Filters.status_update, other_messages))

updater.start_polling()
updater.idle()

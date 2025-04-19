import os
from dotenv import load_dotenv

load_dotenv()

HEADER = int(os.getenv('HEADER', 1024))
FORMAT = os.getenv('FORMAT', 'utf-8')

DISCONNECT_MESSAGE = os.getenv('DISCONNECT_MESSAGE', '!DISCONNECT')
USER_LIST_UPDATE = os.getenv('USER_LIST_UPDATE', '!USER_LIST')
USERNAME_TAKEN = os.getenv('USERNAME_TAKEN', 'Taken')
USERNAME_ACCEPTED = os.getenv('USERNAME_ACCEPTED', 'Ok')

WHISPER_CMD = os.getenv('WHISPER_CMD', '/w')
DM_CMD = os.getenv('DM_CMD', '/dm')

IS_TYPING = os.getenv('IS_TYPING', '/USER_TYPING')
NOT_TYPING = os.getenv('NOT_TYPING', '/USER_NOT_TYPING')
IS_TYPING_LIST = os.getenv('IS_TYPING_LIST', '/USERS_WHO_TYPING')
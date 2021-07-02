import os 
from sys import platform
from koi.models import TransactionReport, TransactionType
from dotenv import load_dotenv, dotenv_values

env = dotenv_values('.env')


class NotificationService():
    def notify_transaction(self, transaction: TransactionReport):
        if not env or not env['PHONE'] or platform != 'darwin': return

        try: os.system(f"osascript sendMessage.scpt {env['PHONE']} '{transaction}' ")
        except Exception as e: print('notify_transaction:error:', e)

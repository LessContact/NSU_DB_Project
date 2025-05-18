import os
from dotenv import load_dotenv

load_dotenv()

DSN_ADMIN = os.getenv('ADMIN_DATABASE_URL')
DSN_HR = os.getenv('HR_DATABASE_URL')

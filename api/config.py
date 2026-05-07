from dotenv import load_dotenv
import os

load_dotenv()

# 지오코더 API KEY
GEO_API_KEY = os.getenv("GEO_API_KEY")

# 오피넷 API KEY
OPINET_KEY = os.getenv("OPINET_KEY")

# 오피넷 API BASE URL
BASE_URL = os.getenv("BASE_URL")

# 지오코더 API KEY 및 load_dotenv 중복 삭제

# Flask flash 메시지, 세션 등에 사용할 secret key
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
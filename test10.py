from dotenv import load_dotenv
import os

load_dotenv()  # 這行要在 os.getenv() 之前執行
print(os.getenv("GEMINI_API_KEY"))  # 應該輸出你的 API 金鑰

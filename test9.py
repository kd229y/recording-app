import time
import requests
from flask import Flask, request
import os
import google.generativeai as genai

# Flask 應用設置
app = Flask(__name__)

# Suno API 基本配置
base_url = 'https://suno-tnavkqq27-makoto-0426s-projects.vercel.app'

# Suno API 函數
def custom_generate_audio(payload):
    url = f"{base_url}/api/custom_generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def extend_audio(payload):
    url = f"{base_url}/api/extend_audio"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def generate_audio_by_prompt(payload):
    url = f"{base_url}/api/generate"
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    return response.json()

def get_audio_information(audio_ids):
    url = f"{base_url}/api/get?ids={audio_ids}"
    response = requests.get(url)
    return response.json()

def get_quota_information():
    url = f"{base_url}/api/get_limit"
    response = requests.get(url)
    return response.json()

# Flask 路由與功能
@app.route('/upload', methods=['POST'])
def upload_audio():
     # 接收並保存上傳的音頻文件
    audio_file = request.files['file']
    audio_path = f'./uploads/{audio_file.filename}'
    audio_file.save(audio_path)

    # 生成 prompt，並通過 Suno API 發送請求
    prompt = generate_prompt(audio_path)
    suno_response = send_to_suno(prompt)
    
    # 打印返回的結果以查看其結構
    print(suno_response)

    # 假設 suno_response 是一個列表，訪問其中的音樂ID
    if isinstance(suno_response, list) and len(suno_response) > 0:
        audio_ids = ','.join([item['id'] for item in suno_response])
        print(f"Audio IDs: {audio_ids}")
        
        # 開始輪詢，檢查音頻狀態
        for _ in range(60):
            audio_data = get_audio_information(audio_ids)
            print(f"Audio status: {audio_data[0]['status']}")
            
            # 如果音頻已生成，返回音頻URL
            if audio_data[0]["status"] == 'streaming':
                audio_url = audio_data[0]['audio_url']
                print(f"Audio URL: {audio_url}")
                return f"Audio available at: {audio_url}"
            
            # 等待5秒後再次檢查
            time.sleep(5)

        return "Audio generation timed out."

    return "Unexpected response from Suno API."
def generate_prompt(audio_path):
    # 配置 Gemini API 密鑰
    os.environ["GEMINI_API_KEY"] = "AIzaSyDO_ycHSv7zjKEYVN1JHvy2LirqTOBy8_E"
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # 生成描述音頻的 prompt
    prompt = "Carefully listen to the following audio file, and generate a prompt that can produce music similar to this piece, and the prompt should including this sentence:do not generate any people voice"

    # 使用 Gemini API 生成 prompt
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    file = genai.upload_file(path=audio_path)
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message([prompt, file])

    return response.text  # 返回文本 prompt

def send_to_suno(prompt):
    # 發送 prompt 到 Suno API 生成音頻
    suno_url = f'{base_url}/api/generate'
    response = requests.post(suno_url, json={"prompt": prompt})
    return response.json()

@app.route('/', methods=['GET'])
def index():
    # 預設首頁，提示如何使用上傳功能
    return '''
        <html>
            <body>
                <h1>Welcome to the Audio Processing API</h1>
                <p>Use the <code>/upload</code> endpoint to upload an audio file.</p>
                <form action="/upload" method="POST" enctype="multipart/form-data">
                    <input type="file" name="file">
                    <input type="submit">
                </form>
            </body>
        </html>
    '''

if __name__ == '__main__':
    # 啟動 Flask 應用
    app.run(debug=True)

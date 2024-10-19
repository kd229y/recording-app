import time
import requests
from flask import Flask, request, render_template_string
import os
import google.generativeai as genai

# Flask 應用設置
app = Flask(__name__, static_folder='static')

# Suno API 基本配置
base_url = 'https://suno-api3-bksggpsz2-makoto-0426s-projects.vercel.app'

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

# 生成 prompt 並顯示在前端表單中
@app.route('/upload', methods=['POST'])
def upload_audio():
    # 接收並保存上傳的音頻文件
    audio_file = request.files['file']
    audio_path = f'./uploads/{audio_file.filename}'
    audio_file.save(audio_path)

    # 生成 prompt
    prompt = generate_prompt(audio_path)

    # 返回一個含有 prompt 的編輯表單
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Generated Prompt</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="text-center">Generated Prompt</h1>
                <div class="text-center">
                </div>
                <form action="/submit_prompt" method="POST" class="mt-4">
                    <div class="form-group">
                        <label for="prompt">Prompt:</label>
                        <textarea class="form-control" name="prompt" rows="10">{{ prompt }}</textarea>
                    </div>
                    <div class="text-center">
                        <input type="submit" class="btn btn-primary" value="Submit to Suno">
                    </div>
                </form>
            </div>
        </body>
        </html>
    ''', prompt=prompt)

# 接收調整後的 prompt 並發送給 Suno API
@app.route('/submit_prompt', methods=['POST'])
def submit_prompt():
    # 獲取用戶修改後的 prompt
    prompt = request.form['prompt']

    # 將 prompt 發送到 Suno API
    suno_response = send_to_suno(prompt)
    
    # 打印返回的結果以查看其結構
    print(suno_response)
    
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
                return f"Audio available at: <a href='{audio_url}'>{audio_url}</a>"
            
            # 等待5秒後再次檢查
            time.sleep(5)

        return "Audio generation timed out."

    return "Unexpected response from Suno API."

def generate_prompt(audio_path):
    # 配置 Gemini API 密鑰
    os.environ["GEMINI_API_KEY"] = "AIzaSyDO_ycHSv7zjKEYVN1JHvy2LirqTOBy8_E"
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # 生成描述音頻的 prompt
    prompt = "Carefully listen to the following audio file, and generate a prompt that can produce music similar to this piece"

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
    try:
        response = requests.post(suno_url, json={"prompt": prompt, "make_instrumental": True})
        
        # 檢查是否成功獲取響應
        if response.status_code == 200:
            try:
                return response.json()  # 嘗試解析 JSON 響應
            except ValueError:
                print("Error: Failed to decode JSON response.")
                return {"error": "Invalid JSON response"}
        else:
            print(f"Error: Received HTTP {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return {"error": "Failed to connect to the API"}

@app.route('/', methods=['GET'])
def index():
    # 預設首頁，提示如何使用上傳功能
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Audio Processing API</title>
            <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1 class="text-center">Welcome to the Audio Processing API</h1>
                <p class="text-center">Use the <code>/upload</code> endpoint to upload an audio file.</p>
                <div class="text-center">
                </div>
                <form action="/upload" method="POST" enctype="multipart/form-data" class="text-center mt-4">
                    <div class="form-group">
                        <input type="file" name="file" class="form-control-file">
                    </div>
                    <button type="submit" class="btn btn-success">Upload</button>
                </form>
            </div>
        </body>
        </html>
    '''

if __name__ == '__main__':
    # 啟動 Flask 應用
    app.run(debug=True)

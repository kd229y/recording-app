from flask import Flask, render_template, request, redirect
import os
app = Flask(__name__)
# 設定錄音檔的儲存路徑
UPLOAD_FOLDER = 'recordings'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload():
    audio_file = request.files['audio_data']
    audio_file.save(os.path.join(UPLOAD_FOLDER, audio_file.filename))
    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)

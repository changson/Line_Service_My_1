from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

Access_Token = os.environ.get("My_Channel_Access_Token")
Channel_Secret = os.environ.get("My_Channel_Secret")
Openaiapi_Key = os.environ.get("My_Openai_Api_Key")

# Channel Access Token
if Access_Token is not None:
    line_bot_api = LineBotApi(Access_Token)
else:
    app.logger.info("Channel_Access_Token missed") 
# Channel Secret
if Channel_Secret is not None:
    handler = WebhookHandler(Channel_Secret)
else:
    app.logger.info("Channel_Secret missed")
# OPENAI API Key初始化設定
if Openaiapi_Key is not None:
    openai.api_key = Openaiapi_Key
else:
    app.logger.info("Openai_Api_Key missed")

# 建立關鍵字和回覆內容的對照表，用來儲存不同的回覆內容
keyword_reply = {
    '你好': '你好，很高興為您服務。',
    '天氣': '今天天氣很好。',
    '打擾': '你好，有什麼需要幫忙的？',
    '謝謝': '不客氣，還有什麼需要幫忙的？'
}

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer

# 定義接收訊息的函數，用來處理 LINE 傳送過來的訊息
@app.route("/", methods=['POST'])
def webhook():
    # 取得 LINE 傳送的訊息內容，並轉換為文字格式
    body = request.get_data(as_text=True)
    # 用 handler 處理訊息，並傳入訊息內容和簽名
    handler.handle(body, request.headers['X-Line-Signature'])
    # 回傳 OK 字串，表示處理成功
    return 'OK'

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息，定義處理訊息的函數，用來根據訊息內容回覆訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # 取得使用者傳送的文字，並儲存在 user_message 變數中
    user_message = event.message.text
    # 預設回覆內容為 None，表示沒有回覆內容
    reply_message = None
    # 逐一檢查關鍵字和回覆內容的對照表
    for keyword in keyword_reply:
        # 如果使用者傳送的文字包含關鍵字
        if keyword in user_message:
            # 將回覆內容設為對應的值，並儲存在 reply_message 變數中
            reply_message = keyword_reply[keyword]
            # 跳出迴圈，不再檢查其他關鍵字
            break
    # 如果沒有找到符合的關鍵字
    if reply_message is None:
        # 將回覆內容設為預設值，表示不明白使用者的意思
        reply_message = '抱歉，我不太明白您的意思。'
    # 用 line_bot_api 回覆訊息，並傳入回覆的代碼和回覆的內容
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )


    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

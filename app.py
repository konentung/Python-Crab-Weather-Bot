from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
    TextMessage
)
import os
import pandas as pd
#Azure CLU
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_messsage(event):
    messages = event.message.text
    if messages == "空氣品質":
        data = import_data()
        county_list = distinct_county(data)
        items = []
        for i in range(0, len(county_list)-9):
            items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label=county_list[i],
                        data=county_list[i]
                    )
                )
            )
        quick_reply = QuickReply(items=items)
        messages = [TextMessage(text="請選擇縣市", quick_reply=quick_reply)]
        reply_message(event, messages)
    else:
        messages = [TextMessage(text=event.message.text)]
        reply_message(event, messages)
    
def reply_message(event, messages):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )

def import_data():
    url = "https://data.moenv.gov.tw/api/v2/aqx_p_02?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=datacreationdate desc&format=CSV"
    url = url.replace(" ", "%20")
    data = pd.read_csv(url, encoding="utf-8")
    data = pd.DataFrame(data)
    return data

def distinct_county(data):
    county_list = list(data.county.unique())
    return county_list

def select_county(data, county):
    data = data[data["county"] == county]
    return data
        
if __name__ == "__main__":
    app.run()
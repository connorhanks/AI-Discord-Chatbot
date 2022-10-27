from neuralintents import GenericAssistant
import random
import requests
import json
import websocket
import time
import os
import time
import threading
from tasksio import TaskPool

# For each token, check its length and append it to the validTokens if it meets requirements
def verifyAndUpdateTokens(tokens):
    validTokens = []
    for token in tokens:
        if len(token) == 70:
            validTokens.append(token)
    print(f"Found {len(validTokens)} valid tokens")

    with open("tokens.txt", "r+") as file:
        # Erase contents
        file.truncate(0)
        for token in validTokens:
            # Write tokens to file
            if token != validTokens[-1]:
                file.write(token+'\n')
            else:
                # If it's the last token, don't add a new line
                file.write(token)
    file.close()

def exitApp():
    input("Press enter to exit...")
    exit()

if not os.path.exists("tokens.txt"):
    print("tokens.txt not found, please add your token(s) to tokens.txt")
    exitApp()
else:
    with open("tokens.txt", "r") as file:
        TOKENS = file.read().splitlines()
        if len(TOKENS) == 0:
            print("No tokens found in tokens.txt")
            exitApp()
        elif len(TOKENS) == 1:
            print(f"Found 1 token in tokens.txt")
        elif len(TOKENS) > 1:
            print(f"Found {len(TOKENS)} tokens in tokens.txt")
    file.close()
    
    # Update tokens.txt upon checking each token is valid
    verifyAndUpdateTokens(TOKENS)
    
    # Train AI model using intents file
    chatbot = GenericAssistant('.\intents\english.json')
    chatbot.train_model()
    chatbot.save_model()

    def send_json_request(ws, request):
            ws.send(json.dumps(request))

    def receive_json_response(ws):
        response = ws.recv()
        if response:
            return json.loads(response)

    # Used to keep the connection alive
    def heartbeat(interval, ws):
        print("Heartbeat begin")
        while True:
            time.sleep(interval)
            heartbeatJSON = {
                "op": 1,
                "d": "null"
            }
            send_json_request(ws, heartbeatJSON)
            print("Heartbeat sent")

    # Create websocket and connect to Discord's gateway
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=6&encording=json')
    event = receive_json_response(ws)
    
    # Set the heartbeat interval
    heartbeat_interval = event['d']['heartbeat_interval'] / 1000
    threading._start_new_thread(heartbeat, (heartbeat_interval, ws))

    while True:
        with open("tokens.txt", "r") as file:
            TOKENS = file.read().splitlines()
            for token in TOKENS:
                # The payload is the data that will be sent to Discord
                payload = {
                    'op': 2,
                    "d": {
                        "token": token,
                        "properties": {
                            "$os": "windows",
                            "$browser": "chrome",
                            "$device": 'pc'
                        }
                    }
                }

                # Connect to Discord using the token
                send_json_request(ws, payload)
                event = receive_json_response(ws)

                try:
                    author = f"{event['d']['author']['username']}"
                    message = f"{event['d']['author']['username']}: {event['d']['content']}"
                    content = f"{event['d']['content']}"
                    channel_id = f"{event['d']['channel_id']}"
                    print(message)

                    # Generates a response to the user's message
                    botResponse = chatbot.request(message)

                    # Generates a delay based on received message length
                    responseDelay = 1
                    if len(botResponse) <= 25:
                        responseDelay = random.randint(0, 5)
                    elif len(botResponse) <= 50:
                        responseDelay = random.randint(5, 10)
                    elif len(botResponse) <= 75:
                        responseDelay = random.randint(10, 12)
                    else:
                        responseDelay = random.randint(12, 15)

                    header = {
                        'authorization': token
                    }
                    payload = {
                        # The content is the message that will be sent to the channel/user
                        'content': botResponse
                    }

                    # Waits before sending the message
                    time.sleep(responseDelay)

                    # Sends the message
                    r = requests.post(
                        "https://discord.com/api/v9/channels/" + channel_id + "/messages", data=payload, headers=header)

                    op_code = event('op')
                    if op_code == 11:
                        print('Heartbeat received')
                except:
                    pass
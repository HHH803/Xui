#This is an example that uses the websockets api and the SaveImageWebsocket node to get images directly without
#them being saved to disk

import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import os
import sys
import uuid
import json
import urllib.request
import urllib.parse

import gradio as gr

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

client_id = str(uuid.uuid4())

# #set the text prompt for our positive CLIPTextEncode
# prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

# import random
# seed = random.randint(1, 2 ** 32 - 1)
# #set the seed for our KSampler node
# prompt["3"]["inputs"]["seed"] = seed


def queue_prompt(prompt, url):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(url), data=data)
    return json.loads(urllib.request.urlopen(req).read())

# def get_image(filename, subfolder, folder_type):
#     data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
#     url_values = urllib.parse.urlencode(data)
#     with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
#         return response.read()

# def get_history(prompt_id):
#     with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
#         return json.loads(response.read())

def get_images(ws, prompt, url):
    prompt_id = queue_prompt(prompt, url)['prompt_id']
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        current_node = data['node']
        else:
            if current_node == 'save_image_websocket_node':
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output

    return output_images


def inference_iamge(url, style_name, 
                    progress=gr.Progress(),
                    ):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, '..', 'workflow_api', f'{style_name}.json')

    with open(json_path, 'r', encoding='utf-8') as file:
        prompt = json.load(file)
    # #set the text prompt for our positive CLIPTextEncode
    # prompt["6"]["inputs"]["text"] = "masterpiece best quality man"

    # import random
    # seed = random.randint(1, 2 ** 32 - 1)
    # #set the seed for our KSampler node
    # prompt["3"]["inputs"]["seed"] = seed

    prompt = change_json_file(prompt)

    server_address=url
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(url, client_id))

    
    images = get_images(ws, prompt, url)

    process_message = ws.recv()

    if process_message["type"] == "status":
        progress(0, desc="Loading Model...")

    if process_message["type"] == "progress" and process_message["data"]["node"] == "3":
        progress(process_message["data"]["value"] / process_message["data"]["max"], 
                    desc="Progressing",)
    

    for node_id in images:
        for image_data in images[node_id]:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))

    return image


if __name__ == "__main__":
    from change_json import change_json_file    
    server_address = "127.0.0.1:8188"

    image = inference_iamge(server_address, "无")

    image.show()
else:
    from modules.change_json import change_json_file

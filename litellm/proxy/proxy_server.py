import sys, os
sys.path.insert(
    0, os.path.abspath("../..")
)  # Adds the parent directory to the system path

try:
    import uvicorn
    import fastapi
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn", "fastapi"])
print()
print("\033[1;31mGive Feedback / Get Help: https://github.com/BerriAI/litellm/issues/new\033[0m")
print()
print()

import litellm
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

user_api_base = None
user_model = None
user_debug = False
user_max_tokens = None
user_temperature = None
user_telemetry = False

#### HELPER FUNCTIONS ####
def print_verbose(print_statement):
    global user_debug 
    print(f"user_debug: {user_debug}")
    if user_debug: 
         print(print_statement)

def usage_telemetry(): # helps us know if people are using this feature. Set `litellm --telemetry False` to your cli call to turn this off
    if user_telemetry: 
        data = {
            "feature": "local_proxy_server"
        }
        litellm.utils.litellm_telemetry(data=data)

def initialize(model, api_base, debug, temperature, max_tokens, telemetry):
    global user_model, user_api_base, user_debug, user_max_tokens, user_temperature, user_telemetry
    user_model = model
    user_api_base = api_base
    user_debug = debug
    user_max_tokens = max_tokens
    user_temperature = temperature
    user_telemetry = telemetry
    usage_telemetry()

# for streaming
def data_generator(response):
    print("inside generator")
    for chunk in response:
        print(f"chunk: {chunk}")
        print_verbose(f"returned chunk: {chunk}")
        yield f"data: {json.dumps(chunk)}\n\n"

#### API ENDPOINTS ####
@app.get("/models") # if project requires model list 
def model_list(): 
    return dict(
        data=[{"id": user_model, "object": "model", "created": 1677610602, "owned_by": "openai"}],
        object="list",
    )

@app.post("/completions")
async def completion(request: Request):
    data = await request.json()
    print_verbose(f"data passed in: {data}")
    if (user_model is None):
        raise ValueError("Proxy model needs to be set")
    data["model"] = user_model
    if user_api_base:
        data["api_base"] = user_api_base
    response = litellm.text_completion(**data)
    if 'stream' in data and data['stream'] == True: # use generate_responses to stream responses
        return StreamingResponse(data_generator(response), media_type='text/event-stream')
    return response

@app.post("/chat/completions")
async def chat_completion(request: Request):
    data = await request.json()
    print_verbose(f"data passed in: {data}")
    if (user_model is None):
        raise ValueError("Proxy model needs to be set")
    data["model"] = user_model

    # override with user settings
    if user_temperature: 
        data["temperature"] = user_temperature
    if user_max_tokens: 
        data["max_tokens"] = user_max_tokens
    if user_api_base: 
        data["api_base"] = user_api_base


    response = litellm.completion(**data)
    if 'stream' in data and data['stream'] == True: # use generate_responses to stream responses
        print("reaches stream")
        return StreamingResponse(data_generator(response), media_type='text/event-stream')
    print_verbose(f"response: {response}")
    return response
import requests
from enum import Enum
import asyncio

HACHIMI_API_URL = "http://localhost:50433"

class RequestType(Enum):
    ReloadLocalizedData = "ReloadLocalizedData"
    StoryGotoBlock = "StoryGotoBlock"


def send_request(type: RequestType, fields: dict, blocking: bool=False) -> requests.Response:
    headers = {
        "content-type": "application/json"
    }

    data = {
        "type": type.value,
    }
    data.update(fields)

    print("Hachimi API request: ", data)

    if blocking:
        return requests.post(HACHIMI_API_URL, headers=headers, json=data, timeout=60)
    
    event_loop = asyncio.get_event_loop()
    event_loop.run_in_executor(None, lambda: requests.post(HACHIMI_API_URL, headers=headers, json=data, timeout=60))
    return None

    # response = requests.post(HACHIMI_API_URL, headers=headers, json=data, timeout=60)
    # return response

def reload_localized_data(blocking: bool = False) -> requests.Response:
    return send_request(RequestType.ReloadLocalizedData, {}, blocking)

def story_goto_block(block_id: int, incremental: bool = True, blocking: bool = False) -> requests.Response:
    fields = {
        "block_id": block_id,
        "incremental": incremental
    }
    return send_request(RequestType.StoryGotoBlock, fields, blocking)

def hello_world() -> requests.Response:
    return requests.get(HACHIMI_API_URL)

def main():
    print(hello_world().json())
    # print(reload_localized_data().json())
    # print(story_goto_block(1).json())

if __name__ == "__main__":
    main()

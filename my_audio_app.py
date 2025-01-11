from   dotenv import load_dotenv
import os
import base64
import asyncio
from   openai import AsyncOpenAI
from   openai.types.beta.realtime.session import Session
from   openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

class RealtimeApp():

    client:             AsyncOpenAI
    should_send_audio:  asyncio.Event
    audio_player:       AudioPlayerAsync
    last_audio_item_id: str | None
    connection:         AsyncRealtimeConnection | None
    session:            Session | None
    connected:          asyncio.Event

    def __init__(self) -> None:
        self.connection         = None
        self.session            = None
        self.client             = AsyncOpenAI()
        self.audio_player       = AudioPlayerAsync()
        self.last_audio_item_id = None
        self.should_send_audio  = asyncio.Event()
        self.connected = asyncio.Event()
print("Start...")
load_dotenv()
print("Environment loaded")
myRealtimeApp: RealtimeApp();

print("End.")

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
    ##audio_player:       AudioPlayerAsync
    last_audio_item_id: str | None
    connection:         AsyncRealtimeConnection | None
    session:            Session | None
    connected:          asyncio.Event

    def __init__(self) -> None:
        self.connection         = None
        self.session            = None
        self.client             = AsyncOpenAI()
        #self.audio_player       = AudioPlayerAsync()
        self.last_audio_item_id = None
        self.should_send_audio  = asyncio.Event()
        self.connected = asyncio.Event()

    async def run(self) -> None:
        print("run() called.")
        connection_handler = self.handle_realtime_connection()
        print("connection_handler started")
        await connection_handler
        print("run() completed.")
        
    async def handle_realtime_connection(self) -> None:
        async with self.client.beta.realtime.connect(model="gpt-4o-realtime-preview-2024-10-01") as conn:
            self.connection = conn
            self.connected.set()

            # note: this is the default and can be omitted
            # if you want to manually handle VAD yourself, then set `'turn_detection': None`
            await conn.session.update(session={"turn_detection": {"type": "server_vad"}})

            acc_items: dict[str, Any] = {}

            async for event in conn:
                print("event.type=", event.type);
                if event.type == "session.created":
                    self.session = event.session
                    assert event.session.id is not None
                    print("session_id=",event.session_id)
                    continue

                if event.type == "session.updated":
                    self.session = event.session
                    continue

                if event.type == "response.audio.delta":
                    if event.item_id != self.last_audio_item_id:
                        self.audio_player.reset_frame_count()
                        self.last_audio_item_id = event.item_id

                    bytes_data = base64.b64decode(event.delta)
                    self.audio_player.add_data(bytes_data)
                    continue

                if event.type == "response.audio_transcript.delta":
                    try:
                        text = acc_items[event.item_id]
                    except KeyError:
                        acc_items[event.item_id] = event.delta
                    else:
                        acc_items[event.item_id] = text + event.delta
                    continue


print("Start.")
load_dotenv()
print("Environment loaded.")
myRealtimeApp = RealtimeApp();
print("Ready to run.")
myRealtimeApp.run()
print("End.")

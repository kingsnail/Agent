from   dotenv import load_dotenv
import os
import base64
import asyncio
from   openai import AsyncOpenAI
from   openai.types.beta.realtime.session import Session
from   openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from typing import Any, cast

class RealtimeApp():

    client:             AsyncOpenAI
    should_send_audio:  asyncio.Event
    ##audio_player:       AudioPlayerAsync
    last_audio_item_id: str | None
    connection:         AsyncRealtimeConnection | None
    session:            Session | None
    connected:          asyncio.Event
    
    def __init__(self) -> None:
        self.connection          = None
        self.session             = None
        self.client              = AsyncOpenAI()
        #self.audio_player       = AudioPlayerAsync()
        self.last_audio_item_id  = None
        self.should_send_audio   = asyncio.Event()
        self.connected           = asyncio.Event()
        self.SAMPLE_RATE         = 48000

    async def run(self) -> None:
        print("run() called.")
        result = await asyncio.gather(self.handle_realtime_connection(), self.send_mic_audio())
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
                    print("session_id=",event.session.id)
                    self.should_send_audio.set()
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
    
    async def _get_connection(self) -> AsyncRealtimeConnection:
        await self.connected.wait()
        assert self.connection is not None
        return self.connection
        
    async def send_mic_audio(self) -> None:
        import sounddevice as sd  # type: ignore

        sent_audio = False

        device_info = sd.query_devices()
        print("device_info:")
        print(device_info)

        read_size = int(self.SAMPLE_RATE * 0.02)

        stream = sd.InputStream(
            channels=1,
            samplerate=self.SAMPLE_RATE,
            dtype="int16",
            #device=DEVICE_INDEX,
        )
        stream.start()

        try:
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0)
                    continue

                print("await send audio.")
                await self.should_send_audio.wait()
                print("proceed send audio.")

                data, _ = stream.read(read_size)

                connection = await self._get_connection()
                if not sent_audio:
                    asyncio.create_task(connection.send({"type": "response.cancel"}))
                    sent_audio = True

                await connection.input_audio_buffer.append(audio=base64.b64encode(cast(Any, data)).decode("utf-8"))

                await asyncio.sleep(0)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()


async def main():
    print("Start.")
    load_dotenv()
    print("Environment loaded.")
    myRealtimeApp = RealtimeApp();
    print("Ready to run.")
    task = myRealtimeApp.run()
    await task
    print("End.")

asyncio.run(main())

from   dotenv import load_dotenv
import os
import base64
import asyncio
from   openai import AsyncOpenAI
from   openai.types.beta.realtime.session import Session
from   openai.resources.beta.realtime.realtime import AsyncRealtimeConnection

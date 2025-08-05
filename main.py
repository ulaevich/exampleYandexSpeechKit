import asyncio
from recognizer import (
    get_recognition_results,
    get_status,
    load_audio_file,
    recognize_audio,
)
from dotenv import load_dotenv
import os

load_dotenv()


async def main():

    token = os.getenv("YANDEX_API_TOKEN")

    content = await load_audio_file("audio.ogg")
    operation_id = await recognize_audio(
        token=token, content_b64=content, language="ru-RU"
    )

    while True:
        status = await get_status(token, operation_id)
        if status.get("done"):
            text = await get_recognition_results(token, operation_id)
            print(text)
            return
        else:
            print("Waiting for recognition to complete...")
            await asyncio.sleep(5)


asyncio.run(main())

import json
import base64
import time

import httpx
import aiofiles

import json
import httpx
import asyncio


async def load_audio_file(filename="audio.ogg"):
    async with aiofiles.open(filename, "rb") as f:
        return base64.b64encode(await f.read()).decode("utf-8")


async def recognize_audio(token: str, content_b64: str, language: str = "ru-RU"):
    headers = {"Authorization": f"Api-Key {token}"}
    body = {
        "content": content_b64,
        "recognitionModel": {
            "model": "general",
            "audioFormat": {"containerAudio": {"containerAudioType": "OGG_OPUS"}},
            "textNormalization": {
                "textNormalization": "TEXT_NORMALIZATION_ENABLED",
                "profanityFilter": False,
                "literatureText": False,
                "phoneFormattingMode": "PHONE_FORMATTING_MODE_DISABLED",
            },
            "languageRestriction": {
                "restrictionType": "WHITELIST",
                "languageCode": [language],
            },
            "audioProcessingType": "FULL_DATA",
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://stt.api.cloud.yandex.net/stt/v3/recognizeFileAsync",
            headers=headers,
            json=body,
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to start recognition: {response.text}")
        return response.json().get("id")


async def get_status(iam_token: str, operation_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"https://operation.api.cloud.yandex.net/operations/{operation_id}",
            headers={"Authorization": f"Api-Key {iam_token}"},
        )
        return response.json()


async def get_recognition_results(iam_token: str, operation_id: str):
    headers = {"Authorization": f"Api-Key {iam_token}"}
    params = {"operationId": operation_id}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://stt.api.cloud.yandex.net/stt/v3/getRecognition",
            headers=headers,
            params=params,
        )

        texts = set()
        for line in response.text.splitlines():
            try:
                data = json.loads(line)
                result = data.get("result", {})

                if "final" in result:
                    for alt in result["final"].get("alternatives", []):
                        texts.add(alt["text"])

            except (json.JSONDecodeError, KeyError, AttributeError):
                continue

        return list(texts)

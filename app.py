import os
import json
import base64
import asyncio
from typing import Optional

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.websockets import WebSocketDisconnect
from dotenv import load_dotenv
from twilio.twiml.voice_response import VoiceResponse, Connect

from urllib.parse import urlparse

from ulaw import ulaw_bytes_to_pcm16
from azure_stt import AzureSTTStream
from azure_llm import generate_reply
from azure_tts import synthesize_mulaw_8khz

load_dotenv()

PORT = int(os.getenv("PORT", 5050))
PUBLIC_HOSTNAME = os.getenv("PUBLIC_HOSTNAME")
SYSTEM_MESSAGE = os.getenv("SYSTEM_MESSAGE", "You are a helpful voice assistant.")

app = FastAPI(title="Twilio Media Stream ↔ Azure Speech/OpenAI")


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server with fastAPI is running!"}


@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Return TwiML that connects the call to our WebSocket media stream."""
    # host = PUBLIC_HOSTNAME or request.url.hostname
    raw_host = PUBLIC_HOSTNAME or request.url.hostname
    parsed = urlparse(raw_host)
    print(f"Incoming call, using host: {raw_host} → {parsed}")
    host = parsed.netloc or parsed.path

    vr = VoiceResponse()
    vr.say(
        # "Please wait while we connect you to our AI assistant. You can start talking after the beep.",
        "You can start talking after the beep.",
    )
    vr.pause(length=1)
    vr.say("Beep.")
    # print("Beep")
    connect = Connect()
    print(f"wss://{host}/media-stream")
    connect.stream(url=f"wss://{host}/media-stream")
    vr.append(connect)

    # return HTMLResponse(content=str(vr), media_type="application/xml")
    return Response(content=str(vr), media_type="application/xml")


@app.websocket("/media-stream")
async def media_stream(ws: WebSocket):
    await ws.accept()
    print("[WS] Twilio connected")

    stt = AzureSTTStream()
    send_lock = asyncio.Lock()
    stream_sid: Optional[str] = None

    async def send_audio_to_twilio(mulaw_bytes: bytes):
        """Send μ-law 8 kHz bytes back to the caller via Twilio media events."""
        if not mulaw_bytes:
            return
        CHUNK = 1600  # ≈200 ms at 8k/8-bit; small chunks = smoother playback
        for i in range(0, len(mulaw_bytes), CHUNK):
            chunk = mulaw_bytes[i : i + CHUNK]
            payload = base64.b64encode(chunk).decode("utf-8")
            msg = {
                "event": "media",
                "media": {"payload": payload},
            }
            # Include streamSid if we have it (recommended by Twilio)
            if stream_sid:
                msg["streamSid"] = stream_sid
            async with send_lock:
                await ws.send_json(msg)
            # Gentle pacing to avoid buffers growing; tune as needed
            await asyncio.sleep(0.02)

    async def rx_loop():
        """Receive Twilio frames → decode → push to Azure STT."""
        nonlocal stream_sid
        try:
            async for text in ws.iter_text():
                data = json.loads(text)
                evt = data.get("event")

                if evt == "start":
                    stream_sid = (data.get("start") or {}).get("streamSid")
                    print(f"[WS] Stream started: {stream_sid}")
                elif evt == "media":
                    b64 = data["media"]["payload"]
                    ulaw = base64.b64decode(b64)
                    pcm16 = ulaw_bytes_to_pcm16(ulaw)
                    stt.push_pcm16(pcm16)
                elif evt == "mark":
                    # Not used in this minimal sample (kept for future barge-in)
                    pass
                elif evt == "stop":
                    print("[WS] Stream stopped by Twilio")
                    break
        except WebSocketDisconnect:
            print("[WS] Client disconnected")
        except Exception as e:
            print("[WS] rx_loop error:", e)
        finally:
            stt.stop()

    async def nlu_tts_loop():
        """Wait for final transcripts → LLM → TTS → stream back audio."""
        try:
            while True:
                await asyncio.sleep(0.01)
                text = stt.get_next_final(timeout=0.0)
                if text is None:
                    # STT canceled or stopped
                    print("[NLU] STT signaled end")
                    break
                if not text:
                    continue

                print("[ASR] User:", text)

                try:
                    reply = generate_reply(text)
                except Exception as e:
                    print("[LLM] Error:", e)
                    reply = "Sorry, I had trouble understanding. Could you rephrase?"

                print("[TTS] Bot:", reply)

                try:
                    mulaw = synthesize_mulaw_8khz(reply)
                    # test = synthesize_mulaw_8khz("Hello, testing one two three")
                    # print("Bytes length:", len(mulaw))
                    # print("First 20 bytes:", mulaw[:20])
                    await send_audio_to_twilio(mulaw)
                except Exception as e:
                    print("[TTS] Error:", e)
        except Exception as e:
            print("[NLU] Loop error:", e)

    await asyncio.gather(rx_loop(), nlu_tts_loop())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
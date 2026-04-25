import asyncio
import json
import websockets
import os

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")

SARVAM_WS_URL = (
    "wss://api.sarvam.ai/speech-to-text-streaming/transcribe/ws"
    "?api_subscription_key={key}"
    "&language_code=gu-IN"
    "&model=saaras:v3"
    "&mode=codemix"
    "&sample_rate=8000"
    "&input_audio_codec=pcm_s16le"
).format(key=SARVAM_API_KEY)

async def handle_vapi_connection(vapi_ws):
    print("✅ Vapi connected")
    try:
        async with websockets.connect(SARVAM_WS_URL) as sarvam_ws:
            print("✅ Connected to Sarvam AI")

            async def vapi_to_sarvam():
                async for message in vapi_ws:
                    if isinstance(message, bytes):
                        await sarvam_ws.send(message)

            async def sarvam_to_vapi():
                async for message in sarvam_ws:
                    if isinstance(message, str):
                        data = json.loads(message)
                        transcript = data.get("transcript", "")
                        is_final = data.get("is_final", False)
                        if transcript:
                            await vapi_ws.send(json.dumps({
                                "type": "transcript",
                                "role": "user",
                                "transcriptType": "final" if is_final else "partial",
                                "transcript": transcript
                            }))
                            print(f"📝 {'FINAL' if is_final else 'partial'}: {transcript}")

            await asyncio.gather(vapi_to_sarvam(), sarvam_to_vapi())

    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 Bridge server starting on port {port}")
    async with websockets.serve(handle_vapi_connection, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

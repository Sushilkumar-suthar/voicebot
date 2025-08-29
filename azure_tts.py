import os
import audioop
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
VOICE = os.getenv("AZURE_TTS_VOICE", "en-US-JennyNeural")

# Produce audio in the exact format Twilio expects for Media Streams backchannel: 8 kHz, 8‑bit μ-law
OUTPUT_FORMAT = speechsdk.SpeechSynthesisOutputFormat.Raw8Khz16BitMonoPcm


# def synthesize_mulaw_8khz(text: str) -> bytes:
#     speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
#     speech_config.speech_synthesis_voice_name = VOICE
#     speech_config.set_speech_synthesis_output_format(OUTPUT_FORMAT)

#     synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
#     result = synthesizer.speak_text_async(text).get()

#     if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
#         detail = result.cancellation_details if result.cancellation_details else "unknown"
#         raise RuntimeError(f"TTS failed: {detail}")

#     return result.audio_data  # Already μ-law 8k bytes

def synthesize_mulaw_8khz(text: str) -> bytes:
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = VOICE
    # Ask Azure for PCM (16-bit, 16kHz mono)
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
    )

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        detail = result.cancellation_details if result.cancellation_details else "unknown"
        raise RuntimeError(f"TTS failed: {detail}")

    pcm16 = result.audio_data  # 16-bit PCM @ 16kHz
    # Step 1: Downsample to 8kHz
    pcm16_8k = audioop.ratecv(pcm16, 2, 1, 16000, 8000, None)[0]
    # Step 2: Convert PCM16 → μ-law
    mulaw_8k = audioop.lin2ulaw(pcm16_8k, 2)

    # print("Bytes length:", len(mulaw_8k))
    # print("First 20 bytes:", mulaw_8k[:20])
    return mulaw_8k

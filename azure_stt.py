import os
import threading
import queue
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import ResultReason
from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

class AzureSTTStream:
    """Push μ-law decoded PCM16 into Azure STT and get final transcripts via a thread-safe queue."""

    def __init__(self):
        # 8 kHz, 16-bit, mono PCM
        fmt = speechsdk.audio.AudioStreamFormat(samples_per_second=8000, bits_per_sample=16, channels=1)
        self.push_stream = speechsdk.audio.PushAudioInputStream(stream_format=fmt)
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)
        print("Starting Azure STT...")
        print(f"Using Azure Speech region: {SPEECH_REGION}, key: {SPEECH_KEY}****")
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language = "en-US"  # change as needed
        # Optional: improved telephony
        speech_config.enable_audio_logging()  # remove in prod if not needed

        self.recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=self.audio_config)

        self.results = queue.Queue()
        self._stopped = threading.Event()

        # Wire events
        def recognized(evt: speechsdk.SpeechRecognitionEventArgs):
            if evt.result.reason == ResultReason.RecognizedSpeech and evt.result.text:
                # Final results only (use Recognizing for partials if you want)
                self.results.put(evt.result.text)

        def canceled(evt: speechsdk.SpeechRecognitionCanceledEventArgs):
            self.results.put(None)  # signal end/error

        self.recognizer.recognized.connect(recognized)
        self.recognizer.canceled.connect(canceled)

        # Start continuous recognition in background thread
        self.recognizer.start_continuous_recognition_async().get()

    def push_pcm16(self, data: bytes):
        if not self._stopped.is_set():
            self.push_stream.write(data)

    def stop(self):
        if not self._stopped.is_set():
            self._stopped.set()
            try:
                self.push_stream.close()
            finally:
                self.recognizer.stop_continuous_recognition_async().get()

    def get_next_final(self, timeout: float = 0.0):
        try:
            return self.results.get(timeout=timeout)
        except queue.Empty:
            return ""
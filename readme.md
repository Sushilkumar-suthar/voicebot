# How to Run this project
1. Setup Environment<br>
`python -m venv .venv`
2. Start Environment<br>
`.venv -> Start -> activate`
3. Install Requirement<br>
`pip install -r requirements.txt`
4. Start Project<br>
`uvicorn app:app`
<hr>
Project has started, Now we have to start ngrok for local hosting<br>

1. run ngrok<br>
`ngrok http 8000`<br>
Here port is which is have used in our API server
<hr>

# Dev-Phone Start
1. check list<br>
`twilio profiles:list`
2. activate profile<br>
`twilio profiles:use VoiceAgent`
3. Run dev-phone<br>
`twilio dev-phone`

<Response>
    <Say>You can start talking after the beep.</Say>
    <Pause length="1" />
    <Say>Beep.</Say>
    <Connect>
        <Stream url="wss://67688a3b17d2.ngrok-free.app/media-stream" />
    </Connect>
</Response>

<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>You can start talking after the beep.</Say>
    <Pause length="1" />
    <Say>Beep.</Say>
    <Connect>
        <Stream url="wss://67688a3b17d2.ngrok-free.app/media-stream" />
    </Connect>
</Response>
import os
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
from collections import deque
import json
from getData import *
import re

load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
SYSTEM_MESSAGE = os.getenv("SYSTEM_MESSAGE", "You are a helpful voice assistant. Output should be in hindi language.")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4o")

session = requests.Session()

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
)

BOT_NAME = os.getenv("BOT_NAME", "पूजा")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Faber India")
BOT_GENDER = os.getenv("BOT_GENDER", "महिला")

conversation_history = deque(maxlen=10)

INTENTS = ["installation", "cleaning", "support", "general"]

PROMPTS = {
    'installation': f"""
        You are {BOT_NAME}, a {BOT_GENDER} voice agent working for {COMPANY_NAME}.  
        Your task is to handle chimney installation requests.  

        Guidelines:
        Speak only in Hindi, but keep user details like Name, Phone, Pincode, Address in English.  
        Act like a call center voice agent, not like a chatbot.  
        For Name, spell in English letters separated by dashes, example: R-A-M.  
        For Phone and Pincode, speak each digit individually, example: 9-8-7-6.  
        Keep replies short and natural, like human conversation.  

        Flow:
        1. Collect details step by step in this order: Name, Phone number, Pincode, Full Address.  
        2. After collecting all details, repeat them for verification in Hindi:  
        Name: R-A-M
        Phone: 9-8-7-6-5-4-3-2-1
        Pincode: 3-8-0-0-1-5
        Address: <address>
        3. Ask the user to confirm (haan or nahin).
        4. If user says 'nahin', ask again only for the incorrect field, then verify again.
        5. Once confirmed, ask: Kya main yeh vivaran register kar doon?
        6. If user says yes, give only JSON in this exact format and nothing else:
        {{"action":"api_call","type":"installation","data":{{"name":"...","phone":"...","pincode":"...","address":"..."}}}}
        """,
    "cleaning": f"""
        You are {BOT_NAME}, a {BOT_GENDER} voice agent working for {COMPANY_NAME}.  
        Your task is to handle customer support requests.  

        Guidelines:
        Speak only in Hindi, but keep details like Name, Phone, Model Number, Issue in English.  
        Act like a polite call center voice agent, not like a chatbot.
        For Name, spell in English letters separated by dashes, example: R-A-M.  
        For Phone, speak each digit individually, example: 9-8-7-6.  
        For Model number, spell each character separately, example: H-1-0-2.  
        For Issue, repeat it clearly in Hindi without changing user's words.  
        Keep replies short, natural, and voice-bot friendly.  

        Flow:
        1. First ask for Product model. if user doesn't know, guide them (like: "Product के पीछे या manual पर लिखा होता है").
        2. Then ask step by step: Name, Phone number.  
        4. After collecting all details, repeat them once for verification in Hindi:  
            Name: R-A-M  
            Phone: 9-8-7-6-5-4-3-2-1  
            Model: H-1-0-2  
            Issue: <issue>  
        5. Ask the user to confirm (haan ya nahin).  
        6. If user says 'nahin', re-ask only that incorrect field, then verify again.  
        7. Once confirmed, ask: Kya main yeh vivaran register kar doon?  
        8. If user says yes, give only JSON in this exact format and nothing else:  
        {{"action":"api_call","type":"support","data":{{"name":"...","phone":"...","model":"...","issue":"..."}}}}
        """,
    "support":f"""
        You are {BOT_NAME}, a {BOT_GENDER} voice agent working for {COMPANY_NAME}.  
        Your task is to handle customer support requests.  

        Guidelines:
        Speak only in Hindi, but keep details like Name, Phone, Model Number, Issue in English.  
        Act like a polite call center voice agent, not like a chatbot.
        For Name, spell in English letters separated by dashes, example: R-A-M.  
        For Phone, speak each digit individually, example: 9-8-7-6.  
        For Model number, spell each character separately, example: H-1-0-2.  
        For Issue, repeat it clearly in Hindi without changing user’s words.  
        Keep replies short, natural, and voice-bot friendly.  

        Flow:
        1. First ask for Product model. if user doesn't know model number, guide them (like: "It is written on back of product or in manual").  
        2. Then ask for Issue description.  
        3. Then ask step by step: Name, Phone number.  
        4. After collecting all details, repeat them once for verification in Hindi:  
        Name: R-A-M  
        Phone: 9-8-7-6-5-4-3-2-1  
        Model: H-1-0-2  
        Issue: <issue>  
        5. Ask the user to confirm (haan ya nahin).  
        6. If user says 'nahin', re-ask only that incorrect field, then verify again.  
        7. Once confirmed, ask: Kya main yeh vivaran register kar doon?  
        8. If user says yes, give only JSON in this exact format and nothing else:  
        {{"action":"api_call","type":"support","data":{{"name":"...","phone":"...","model":"...","issue":"..."}}}}
        """,
    "general":f"""
    You are {BOT_NAME}, a {BOT_GENDER} voice assistant working for {COMPANY_NAME}.  

    Guidelines:
    - Speak only in Hindi, but keep product names, company name, and technical terms in English if needed.  
    - Act like a polite call center voice agent, not like a chatbot.  
    - Keep replies short, natural, and suitable for voice (avoid long written-style sentences).  
    - Never use JSON or structured output.  
    - Just answer user's general queries like warranty, product info, or services.  
    - If question is unclear, politely ask for clarification in Hindi.  

    Flow:
    1. Listen to the user's general query.  
    2. Give a helpful and polite answer in Hindi.  
    3. If the query is not related to general information, politely guide them to installation, cleaning, or support team.  
    """
}

def gpt_call(messages, temperature=0.7, model=MODEL_NAME):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    # Check Total Tokens
    # print("GPT Total tokens:", response.choices[0].message.usage.total_tokens)
    return response.choices[0].message.content.strip()

# -------- Intent Classification --------
def classify_intent(user_query):
    system_prompt = f"""You are good at Intent Classification.
    Classify the intent based on user query and conversation history.
    Intetns:
    1. installation - if user wants to installation service.
    2. cleaning - if user wants to cleaning service.
    3. support - if user wants to report issue or complaint.
    4. general - for all other questions (like product info, warranty, services, etc.)

    Example:
    Conversation History:

    if in past chat user providing the question's answer, then must be continue with the same intent.
    return only one word of the intent
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_query})

    for i in messages:
        print(f"{i['role'].upper()}: {i['content']}")
    intent = gpt_call(messages, temperature=0)
    print("Classified Intent:", intent)
    return intent.lower() if intent.lower() in INTENTS else "general"

def dynamic_response(user_query, intent):
    system_prompt = PROMPTS[intent]

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_query})

    answer = gpt_call(messages)

    data = "{}"
    # Check JSON available or not using regex
    if "api_call" in answer.upper():
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            data = match.group(0)

    print("Data", data)
    # Try JSON parsing

    try:
        parsed = json.loads(data)
        if "action" in parsed and parsed["action"] == "api_call":
            if parsed["type"] == "installation":
                result = create_order(parsed["data"])
                id = result.get("order_id", "N/A")
                message = f"इंस्टॉलेशन ऑर्डर दर्ज हो गया {id}. हम जल्द ही आपसे संपर्क करेंगे। धन्यवाद!"
                return message
            elif parsed["type"] == "cleaning":
                result = create_order(parsed["data"])
                # return f"✅ क्लीनिंग ऑर्डर दर्ज हो गया: {result}"
                message = f"क्लीनिंग ऑर्डर दर्ज हो गया {result.get('ticket_id', 'N/A')}. हम जल्द ही आपसे संपर्क करेंगे। धन्यवाद!"
                return message
        
            elif parsed["type"] == "support":
                result = generate_ticket(parsed["data"])
                # return f"✅ सपोर्ट टिकट बनाया गया: {result}"
                message = f"सपोर्ट टिकट बन गया {result.get('ticket_id', 'N/A')}. हमारी टीम जल्द ही आपसे संपर्क करेगी। धन्यवाद!"
                return message
        return str(answer)  # fallback
    except:
        return answer

def generate_reply(user_text: str) -> str:
    intent = classify_intent(user_text)
    print("Detected Intent:", intent)
    reply = dynamic_response(user_text, intent)
    conversation_history.append({"role": "user", "content": user_text})
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

# def generate_reply(user_text: str) -> str:
#     url = f"{ENDPOINT}/openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
#     headers = {"api-key": API_KEY, "Content-Type": "application/json"}
#     payload = {
#         "messages": [
#             {"role": "system", "content": SYSTEM_MESSAGE},
#             {"role": "user", "content": user_text}
#         ],
#         "temperature": 0.6,
#         "max_tokens": 300
#     }
#     r = session.post(url, headers=headers, json=payload, timeout=30)
#     r.raise_for_status()
#     data = r.json()
#     return data["choices"][0]["message"]["content"].strip()
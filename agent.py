from fastapi import FastAPI,UploadFile, File, UploadFile, BackgroundTasks, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import whisper
import os
import time
import asyncio
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
import torch
from prompt import law_prompt_text
import  asyncio

import pyttsx3
from fastapi.middleware.cors import CORSMiddleware



# App initialization
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # or list of your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],            # <-- this allows OPTIONS, GET, POST, etc.
    allow_headers=["*"],
)


# Directories for uploads and generated audio
UPLOAD_AUDIO_DIR = Path("uploads/audio")
RESPONSE_AUDIO_DIR = Path("static/audio")
for directory in (UPLOAD_AUDIO_DIR, RESPONSE_AUDIO_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load Whisper model once
whisper_model = whisper.load_model("base",device="cuda")

# Initialize TTS engine once
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty("voices")
for v in voices:
    if "male" in v.name.lower() or "male" in v.id:
        tts_engine.setProperty("voice", v.id)
        break



# Initialize LLM and parser
llm = OllamaLLM(model="llama3.2:3B", device=device)
parser = StrOutputParser()

# Build prompt template with history placeholder
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=law_prompt_text),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{query}")
])

# Build chain and wrap with in-memory history
chain = chat_prompt | llm | parser
store: dict[str, ChatMessageHistory] = {}
def get_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversation = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_history,
    input_messages_key="query",
    history_messages_key="history"
)




    
@app.post("/whisper")
async def whisper_endpoint(file: UploadFile = File(...)):
    path = UPLOAD_AUDIO_DIR / file.filename
    try:
        with open(path, "wb") as f:
            f.write(await file.read())
        result = await asyncio.to_thread(whisper_model.transcribe, str(path))
        text = result.get("text", "")
        print(text)
        os.remove(path)
        return JSONResponse({"transcription": text})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(payload: dict = Body(...), background_tasks: BackgroundTasks = None):
    q = payload.get("query")
    if not q:
        raise HTTPException(status_code=400, detail="Query missing")
    session_id = "default_session"

    # Generate LLM response with history
    result = await asyncio.to_thread(
        conversation.invoke,
        {"query": q},
        {"session_id": session_id}
    )
    
    print(f"Query: {q}")
    response_text = result.get("output") if isinstance(result, dict) else str(result)
    response_text = response_text.replace("\n", "").replace("*", " ")
    print(f"Generated response: {response_text}")



    # Queue TTS generation
    ts = int(time.time() * 1000)
    filename = f"response_{ts}.wav"
    out_path = RESPONSE_AUDIO_DIR / filename
    await asyncio.to_thread(generate_audio_from_response, response_text, out_path) 

    return JSONResponse({
        "response": response_text,
        
        "audio_url": f"http://10.7.0.28:1000/static/audio/{filename}"
    })




def generate_audio_from_response(response_text: str, out_path: Path) -> None:
    # 1. New engine for each file
    engine = pyttsx3.init()
    # (Re-apply your male-voice selection if needed)
    for v in engine.getProperty("voices"):
        if "male" in v.name.lower() or "male" in v.id:
            engine.setProperty("voice", v.id)
            break

    engine.save_to_file(response_text, str(out_path))
    engine.runAndWait()
    engine.stop()

    # 2. Flush to disk
    with open(out_path, "rb+") as f:
        f.flush()
        os.fsync(f.fileno())  

    # 3. (Optional) loosen perms if on Unix
    try:
        out_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        pass

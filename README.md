# AI Law Voice Agent

## Project Overview
Law Agent is an AI-powered legal assistant that specializes in providing information about specific Indian Supreme Court cases. The system uses speech recognition, natural language processing, and text-to-speech technologies to create an interactive conversational experience for users seeking legal information.

## Features
- **Speech Recognition**: Converts user's spoken questions into text using Whisper AI
- **Legal Knowledge Base**: Specializes in three landmark Indian Supreme Court cases:
  1. Lalita Kumari v. State of UP (mandatory FIR in cognizable cases)
  2. Mohd. Ahmad Khan v. Shah Bano Begum (Section 125 of CrPC)
  3. D.K. Basu v. State of Bengal (guidelines for rights of arrested persons)
- **Natural Language Processing**: Processes user queries using LLaMA 3.2 (3B parameter model)
- **Text-to-Speech**: Converts AI responses to spoken audio using pyttsx3
- **Conversation Memory**: Maintains context throughout the conversation

## Technical Architecture
- **Backend**: FastAPI web server
- **AI Models**:
  - OpenAI Whisper for speech-to-text
  - LLaMA 3.2 (3B) for natural language processing
- **Speech Synthesis**: pyttsx3 for text-to-speech conversion
- **GPU Acceleration**: CUDA support for faster inference when available

## API Endpoints
- `/whisper`: Transcribes uploaded audio files
- `/ask`: Processes text queries and returns both text and audio responses

## Setup and Requirements
- Python 3.x
- CUDA-compatible GPU (optional but recommended)
- Required Python packages:
  - fastapi
  - whisper
  - langchain
  - langchain_ollama
  - torch
  - pyttsx3

## Usage
1. Start the server
2. Upload audio questions or send text queries
3. Receive detailed responses about the supported legal cases

## Limitations
The system is specifically designed to provide information only about the three included Supreme Court cases and will not answer questions about other legal matters.

## Project Structure
- `agent.py`: Main application code with FastAPI server and endpoints
- `prompt.py`: Contains the system prompt with case information and response guidelines

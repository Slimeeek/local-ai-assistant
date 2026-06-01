# Пользователь просто делает:
git clone https://github.com/Slimeeek/local-ai-assistant.git
cd local-ai-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2:3b
ollama pull nomic-embed-text

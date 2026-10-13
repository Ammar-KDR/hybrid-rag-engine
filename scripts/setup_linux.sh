#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🏛️ PSUT Sovereign Hybrid RAG - Linux Workstation Setup"
echo "=========================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed. Please install Python 3.10+."
    exit 1
fi

echo "📦 Creating virtual environment (.venv)..."
python3 -m venv .venv
source .venv/bin/activate

echo "📦 Upgrading pip and installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Check Ollama
if command -v ollama &> /dev/null; then
    echo "🦙 Ollama detected. Checking background service..."
    if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "Starting Ollama daemon in background..."
        nohup ollama serve > ollama.log 2>&1 &
        sleep 3
    fi
    echo "Pulling qwen3.5:4b..."
    ollama pull qwen3.5:4b || echo "Warning: Ollama pull failed or offline."
else
    echo "⚠️ Ollama is not installed in PATH. Please install Ollama from https://ollama.com."
fi

echo "🌐 Pre-caching multilingual embedding and reranking models..."
export PYTHONPATH="src"
python3 -c "
from sentence_transformers import SentenceTransformer, CrossEncoder
print('Caching paraphrase-multilingual-MiniLM-L12-v2...')
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
print('Caching BAAI/bge-reranker-v2-m3...')
CrossEncoder('BAAI/bge-reranker-v2-m3')
print('Models cached successfully!')
" || echo "Warning: Model pre-caching encountered an error."

echo "✅ Setup complete! You can now run the system using: bash scripts/run_linux.sh"

#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🚀 Starting PSUT Sovereign Hybrid RAG on Linux"
echo "=========================================================="

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

export PYTHONPATH="src"
export OLLAMA_MODEL="qwen3.5:4b"
export EMBEDDING_MODEL_NAME="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
export RERANKER_MODEL_NAME="BAAI/bge-reranker-v2-m3"

# 1. Check Ollama
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "🦙 Starting Ollama daemon..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 3
fi

# 2. Start FastAPI Server in background
echo "⚡ Starting FastAPI Core Engine on http://127.0.0.1:8000..."
nohup python3 -m uvicorn rag.api.app:app --host 127.0.0.1 --port 8000 > fastapi.log 2>&1 &
FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

# Wait for FastAPI startup
echo "Waiting for API readiness..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/v1/health | grep -q '"ready"'; then
        echo "✅ FastAPI is ready!"
        break
    fi
    sleep 1
done

# 3. Start Streamlit UI
echo "🎨 Starting Streamlit Institutional UI on http://localhost:8501..."
python3 -m streamlit run src/rag/ui/app.py --server.port 8501

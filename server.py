from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from legal_agent import LegalGraphPathfinder
import uvicorn

app = FastAPI(title="Legal AI API")

# Cho phep Frontend (Next.js) goi vao
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khoi tao Agent
agent = LegalGraphPathfinder()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = agent.ask(request.message)

        # ask() tra ve tuple (llm_answer, raw_log_lines)
        if isinstance(result, tuple):
            llm_answer, raw_log = result
            reasoning_text = "\n".join(raw_log) if raw_log else ""
        else:
            # Fallback neu tra ve chuoi loi don gian
            llm_answer = result
            reasoning_text = ""

        return {
            "answer": llm_answer,
            "reasoning": reasoning_text
        }
    except Exception as e:
        print(f"[ERROR] Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

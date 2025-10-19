import os 
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vllm import LLM, SamplingParams
from transformers import AutoProcessor
import uuid
import time
from vllm.assets.image import ImageAsset

from PIL import Image
import base64
import io

os.environ["CUDA_VISIBLE_DEVICES"] = "7"

model_input_path = "MODEL_INPUT_PATH"

processor = AutoProcessor.from_pretrained(model_input_path)
llm = LLM(
    model=model_input_path,
    max_model_len=12288,
    tensor_parallel_size=1, 
    trust_remote_code=True
)  

app = FastAPI()

class OpenAIRequest(BaseModel):
    model: str
    messages: list
    max_tokens: int = 12288
    temperature: float = 1.0
    top_p: float = 0.7
    presence_penalty: float = 1.0

@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIRequest):
    try:
        if not request.messages or len(request.messages) == 0:
            raise HTTPException(status_code=400, detail="No messages provided.")

        prompt = processor.apply_chat_template(
            request.messages,
            tokenize=False,
            add_generation_prompt=True,
		)

        inputs = {
            "prompt": prompt,
            "multi_modal_data": {
                "image": Image.open(io.BytesIO(base64.b64decode(request.messages[1]["content"][0]["image"])))
            },
        }

        print(inputs["prompt"])

        sampling_params = SamplingParams(
            max_tokens=request.max_tokens,
            temperature=0.7,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty
        )

        print(sampling_params)

        outputs = llm.generate(inputs, sampling_params)

        response = {
            "id": f"vllm-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": outputs[0].outputs[0].text.strip(),
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Starting server on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
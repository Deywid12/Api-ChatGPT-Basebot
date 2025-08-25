import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_TEXT = os.getenv("MODEL_TEXT", "gpt-5")
MODEL_EMBED = os.getenv("MODEL_EMBED", "text-embedding-3-small")

def embed_texts(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=MODEL_EMBED, input=texts)
    return [d.embedding for d in resp.data]

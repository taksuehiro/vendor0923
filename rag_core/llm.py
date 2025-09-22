from langchain_openai import ChatOpenAI, OpenAIEmbeddings

def get_embeddings(model_name: str, api_key: str):
    return OpenAIEmbeddings(model=model_name, api_key=api_key)

def get_chat(model_name: str, temperature: float, api_key: str):
    return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)
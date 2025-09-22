from typing import Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def load_prompt(prompt_text: str) -> PromptTemplate:
    return PromptTemplate(template=prompt_text, input_variables=["context", "question"])

def make_chain(vectorstore, llm, top_k: int, prompt: PromptTemplate,
               use_mmr: bool = False, score_threshold: Optional[float] = None):
    search_kwargs = {"k": top_k}
    if use_mmr:
        search_kwargs["search_type"] = "mmr"
    if score_threshold is not None:
        search_kwargs["score_threshold"] = score_threshold

    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )
    return chain
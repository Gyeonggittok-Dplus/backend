from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

def welfare_chain(query: str):
    prompt = PromptTemplate.from_template("""
    사용자의 질문에 맞는 복지 혜택을 2~3개 추천해줘.
    각 항목은 이름, 지원대상, 주요내용만 간단히 요약해.
    질문: {query}
    """)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(query)

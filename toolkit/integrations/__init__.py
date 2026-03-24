"""
QALIS Toolkit — LLM Framework Integrations
============================================

Drop-in callbacks and middleware for popular LLM frameworks.

Integrations:
    QALISLangChainCallback    LangChain BaseCallbackHandler — auto-collects
                              QALIS metrics on every LLM chain call.

Usage::

    from toolkit.integrations.langchain_callback import QALISLangChainCallback

    callback = QALISLangChainCallback(system_id="MY_SYS", domain="document_qa")
    chain = RetrievalQA.from_chain_type(llm=llm, callbacks=[callback])

Paper reference: §4.5 (Toolkit Design) — "The toolkit ships with integration
adapters for LangChain, allowing zero-code instrumentation of RAG pipelines."
"""

from toolkit.integrations.langchain_callback import QALISLangChainCallback

__all__ = ["QALISLangChainCallback"]

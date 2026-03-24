"""
QALIS Toolkit
=============

Production-ready metric collection, CI/CD quality gates, and monitoring
integrations for LLM-integrated software systems.

Paper: QUATIC 2025 — QALIS: A Multi-Dimensional Quality Assessment Framework
for Large Language Model-Integrated Software Systems.
Section: §4.5 (Toolkit Design).

Quick start::

    from toolkit.collectors.qalis_collector import QALISCollector

    collector = QALISCollector(
        system_id="my-chatbot",
        domain="customer_support",
        llm_provider="openai"
    )
    result = collector.evaluate(
        query="What is your return policy?",
        response="We accept returns within 30 days.",
        context="Returns policy: items may be returned within 30 days."
    )
    print(result.summary_report())
"""

__version__ = "1.0.0"

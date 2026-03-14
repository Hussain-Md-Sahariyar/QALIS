"""
QALIS LangChain Callback Handler
==================================

Zero-code QALIS instrumentation for LangChain chains and agents.

Attach QALISLangChainCallback to any LangChain chain or agent to
automatically collect QALIS metrics on every LLM call — no changes
to application code required.

The callback captures:
    - Input prompt / query (on_llm_start / on_chain_start)
    - Generated response (on_llm_end)
    - Retrieved context documents (on_retriever_end, for RAG chains)
    - Latency from start to on_llm_end
    - Errors (on_llm_error, on_chain_error)

Collected evaluations are forwarded to a QALISStreamCollector for
asynchronous evaluation and optional Prometheus / MLflow export.

Usage — RAG chain::

    from langchain.chains import RetrievalQA
    from toolkit.integrations.langchain_callback import QALISLangChainCallback

    callback = QALISLangChainCallback(
        system_id="S3_DocQA",
        domain="document_qa",
        llm_provider="google",
    )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        callbacks=[callback],
    )
    response = chain.run("Summarise section 4 of the contract.")

    # Access batch results
    print(callback.stream.buffer_size)   # buffered interactions awaiting flush

Usage — plain LLMChain::

    from langchain.chains import LLMChain
    chain = LLMChain(llm=llm, prompt=prompt, callbacks=[callback])

Usage — attach Prometheus exporter::

    from toolkit.exporters.prometheus_exporter import PrometheusExporter
    exporter = PrometheusExporter(system_id="S3_DocQA", port=9090)
    exporter.start()
    callback.stream.on_flush(exporter.update)

Paper reference: §4.5 (Toolkit Design).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult, Document
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    # Provide a no-op base class so the module can be imported without LangChain
    class BaseCallbackHandler:  # type: ignore[no-redef]
        pass


class QALISLangChainCallback(BaseCallbackHandler):
    """
    LangChain callback handler that transparently instruments LLM chains
    with QALIS quality metrics.

    All metric evaluation is deferred to a QALISStreamCollector background
    flush — there is zero latency overhead on the LLM call itself.

    Args:
        system_id:              QALIS system identifier.
        domain:                 Deployment domain (customer_support |
                                document_qa | code_generation | healthcare).
        llm_provider:           LLM backend name (openai | anthropic | google |
                                self_hosted).
        flush_interval_seconds: How often to flush buffered evaluations (s).
        raise_on_error:         If True, propagate QALIS errors (default False).
        **collector_kwargs:     Additional args forwarded to QALISStreamCollector.
    """

    def __init__(
        self,
        system_id: str,
        domain: str = "general",
        llm_provider: str = "openai",
        flush_interval_seconds: int = 300,
        raise_on_error: bool = False,
        **collector_kwargs: Any,
    ):
        if not _LANGCHAIN_AVAILABLE:
            logger.warning(
                "langchain not installed — QALISLangChainCallback will be a no-op. "
                "Install with: pip install langchain"
            )

        self.system_id = system_id
        self.domain    = domain
        self.raise_on_error = raise_on_error

        # Import here so the module can be loaded without langchain installed
        from toolkit.collectors.qalis_collector import QALISStreamCollector
        self.stream = QALISStreamCollector(
            system_id=system_id,
            domain=domain,
            llm_provider=llm_provider,
            flush_interval_seconds=flush_interval_seconds,
            **collector_kwargs,
        )

        # Per-run state (keyed by run_id UUID)
        self._pending: Dict[str, Dict[str, Any]] = {}

        logger.info(
            "QALISLangChainCallback initialised — system=%s domain=%s",
            system_id, domain,
        )

    # ── LangChain callback overrides ──────────────────────────────────────────

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Record start time and input prompt when LLM is invoked."""
        self._pending[str(run_id)] = {
            "prompt":    "\n".join(prompts),
            "context":   None,
            "t_start":   time.perf_counter(),
        }

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Same as on_llm_start but for chat models."""
        # Flatten message content to a single string
        try:
            flat = "\n".join(
                getattr(m, "content", str(m))
                for msg_list in messages
                for m in msg_list
            )
        except Exception:
            flat = str(messages)
        self._pending[str(run_id)] = {
            "prompt":  flat,
            "context": None,
            "t_start": time.perf_counter(),
        }

    def on_retriever_end(
        self,
        documents: List[Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Capture retrieved documents as grounding context for SF metrics.

        LangChain fires this before on_llm_start in retrieval chains, so we
        store context against the parent_run_id and propagate it to child runs.
        """
        if not documents:
            return
        try:
            context_text = "\n\n".join(
                getattr(doc, "page_content", str(doc)) for doc in documents
            )[:4096]   # cap at 4K chars for NLI model context window
        except Exception:
            context_text = str(documents)[:4096]

        # Store under both run_id and parent_run_id so child LLM runs pick it up
        for rid in (str(run_id), str(parent_run_id)):
            if rid and rid != "None":
                if rid not in self._pending:
                    self._pending[rid] = {}
                self._pending[rid]["context"] = context_text

    def on_llm_end(
        self,
        response: "LLMResult",
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Record the LLM response and submit the interaction for evaluation.

        Extracts the generated text, computes elapsed latency, and records
        the interaction into the QALISStreamCollector buffer.
        """
        state = self._pending.pop(str(run_id), None)
        if state is None:
            logger.debug("on_llm_end: no pending state for run_id=%s", run_id)
            return

        try:
            # Extract generated text
            if response.generations:
                gen = response.generations[0][0]
                response_text = getattr(gen, "text", str(gen))
            else:
                response_text = ""

            latency_ms = (time.perf_counter() - state.get("t_start", 0)) * 1000

            # Propagate context from parent run if not already present
            context = state.get("context")
            if context is None and parent_run_id is not None:
                parent_state = self._pending.get(str(parent_run_id), {})
                context = parent_state.get("context")

            self.stream.record(
                query=state.get("prompt", ""),
                response=response_text,
                context=context,
                latency_ms=latency_ms,
                metadata={
                    "run_id":        str(run_id),
                    "parent_run_id": str(parent_run_id),
                    "llm_provider":  self.domain,
                },
            )

            logger.debug(
                "QALISLangChainCallback: buffered interaction "
                "run_id=%s latency=%.1fms buffer=%d",
                run_id, latency_ms, self.stream.buffer_size,
            )
        except Exception as exc:
            logger.error("on_llm_end error: %s", exc)
            if self.raise_on_error:
                raise

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Clean up pending state on LLM error."""
        self._pending.pop(str(run_id), None)
        logger.warning("LLM error on run_id=%s: %s", run_id, error)

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """
        Capture chain-level inputs (question/query key) for non-LLM chains.

        Only stores a record if no record for this run exists yet — the
        on_llm_start hook is preferred when present.
        """
        if str(run_id) in self._pending:
            return
        # Common input keys in QA chains
        query = (
            inputs.get("question")
            or inputs.get("query")
            or inputs.get("input")
            or str(inputs)[:500]
        )
        self._pending[str(run_id)] = {
            "prompt":  query,
            "context": None,
            "t_start": time.perf_counter(),
        }

    def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Clean up on chain error."""
        self._pending.pop(str(run_id), None)
        logger.warning("Chain error on run_id=%s: %s", run_id, error)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """
        Flush the stream collector and stop the background flush timer.

        Call this at application shutdown to ensure all buffered interactions
        are evaluated before the process exits.
        """
        self.stream.stop()

    @property
    def pending_count(self) -> int:
        """Number of open (started but not completed) LLM runs."""
        return len(self._pending)

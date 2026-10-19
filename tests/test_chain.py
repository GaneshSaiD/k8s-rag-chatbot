from unittest.mock import MagicMock, patch

from backend.rag import chain

CHUNKS = [
    {"text": "Pods restart when the container exits.", "source": "https://k8s.io/pods", "score": 0.9},
    {"text": "Use kubectl logs --previous.", "source": "https://k8s.io/debug", "score": 0.8},
    {"text": "Restart policy defaults to Always.", "source": "https://k8s.io/pods", "score": 0.7},
]


def test_build_context_includes_every_chunk():
    ctx = chain.build_context(CHUNKS)
    assert ctx.count("Source:") == 3
    assert "kubectl logs --previous" in ctx


def test_unique_sources_dedupes_and_keeps_order():
    assert chain.unique_sources(CHUNKS) == ["https://k8s.io/pods", "https://k8s.io/debug"]


@patch.object(chain, "_get_llm")
@patch.object(chain, "_get_retriever")
def test_ask_wires_retriever_and_llm(mock_get_retriever, mock_get_llm):
    mock_get_retriever.return_value = MagicMock(return_value=CHUNKS)
    mock_get_llm.return_value.invoke.return_value = MagicMock(content="Check the logs.")

    result = chain.ask("Why is my pod restarting?")

    assert result == {"answer": "Check the logs.", "sources": ["https://k8s.io/pods", "https://k8s.io/debug"]}
    mock_get_retriever.return_value.assert_called_once_with("Why is my pod restarting?")

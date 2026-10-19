from unittest.mock import patch

from backend.rag import retriever


@patch.object(retriever, "Pinecone")
@patch.object(retriever, "OpenAIEmbeddings")
def test_retrieve_maps_pinecone_matches(mock_embeddings, mock_pinecone):
    mock_embeddings.return_value.embed_query.return_value = [0.1, 0.2]
    mock_pinecone.return_value.Index.return_value.query.return_value = {
        "matches": [{"metadata": {"text": "Pod basics", "source": "https://k8s.io/pods"}, "score": 0.91}]
    }

    retrieve = retriever.get_retriever()
    chunks = retrieve("what is a pod")

    assert chunks == [{"text": "Pod basics", "source": "https://k8s.io/pods", "score": 0.91}]
    mock_pinecone.return_value.Index.return_value.query.assert_called_once()

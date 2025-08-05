class Reranker:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def rerank(self, results: List[dict]) -> List[dict]:
        """Filter results based on similarity threshold."""
        return [result for result in results if result["distance"] < self.threshold]
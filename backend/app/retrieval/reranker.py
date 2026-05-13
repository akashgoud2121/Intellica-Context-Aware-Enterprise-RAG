from typing import List, Dict, Any, Tuple

class EnterpriseReranker:
    @staticmethod
    def rerank_hybrid_results(semantic_results: List[Tuple[Dict[str, Any], float]], 
                              keyword_results: List[Tuple[Dict[str, Any], float]], 
                              alpha: float = 0.7) -> List[Dict[str, Any]]:
        """
        Combines Semantic search scores and Keyword BM25 scores using Reciprocal Rank Fusion / Weighted Sum.
        alpha: weight given to semantic search (1 - alpha for keyword search).
        """
        combined_scores: Dict[str, Dict[str, Any]] = {}

        # Process Semantic Results
        for item, score in semantic_results:
            chunk_id = item["chunk_id"]
            if chunk_id not in combined_scores:
                combined_scores[chunk_id] = {"item": item, "semantic_score": 0.0, "keyword_score": 0.0}
            combined_scores[chunk_id]["semantic_score"] = score

        # Process Keyword Results
        for item, score in keyword_results:
            chunk_id = item["chunk_id"]
            if chunk_id not in combined_scores:
                combined_scores[chunk_id] = {"item": item, "semantic_score": 0.0, "keyword_score": 0.0}
            combined_scores[chunk_id]["keyword_score"] = score

        # Calculate weighted final score
        ranked_list = []
        for chunk_id, entry in combined_scores.items():
            final_score = (alpha * entry["semantic_score"]) + ((1.0 - alpha) * entry["keyword_score"])
            entry["item"]["relevance_score"] = round(final_score, 4)
            ranked_list.append((entry["item"], final_score))

        # Sort descending by final score
        ranked_list.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in ranked_list]

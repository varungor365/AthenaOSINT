"""
RAG Evaluator using Ragas.
Assess the quality (Faithfulness, Answer Relevance) of Jarvis's responses.
"""
from loguru import logger
from config import get_config
import os

class RAGEvaluator:
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.get('OPENAI_API_KEY')
        self.enabled = bool(self.api_key)

    def evaluate(self, question: str, answer: str, context: list):
        """
        Run Ragas evaluation on a single Q&A pair.
        Returns a dictionary of scores.
        """
        if not self.enabled:
            return {"error": "Evaluator disabled (Missing OpenAI Key)"}
        
        try:
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevance
            from datasets import Dataset

            # Prepare dataset format for Ragas
            data = {
                'question': [question],
                'answer': [answer],
                'contexts': [context], # List of lists
            }
            dataset = Dataset.from_dict(data)

            # Run Evaluation
            results = evaluate(
                dataset=dataset,
                metrics=[
                    faithfulness,
                    answer_relevance,
                ]
            )
            
            # Extract scores
            scores = {
                'faithfulness': results['faithfulness'],
                'answer_relevance': results['answer_relevance']
            }
            
            logger.info(f"RAG Evaluation Scores: {scores}")
            return scores

        except Exception as e:
            logger.error(f"RAG Evaluation Failed: {e}")
            return {"error": str(e)}

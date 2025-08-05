from src.retrieval.retriever import Retriever
from src.generation.response_generator import ResponseGenerator
from src.utils.config import load_config
from src.utils.logger import setup_logger

def main():
    config = load_config("configs/config.yaml")
    logger = setup_logger(config)
    
    logger.info("Starting system evaluation...")
    
    retriever = Retriever(
        model_name=config["models"]["embedder"]["name"],
        index_path=config["vector_store"]["index_path"],
        mapping_path=config["vector_store"]["chunk_mapping"],
        top_k=config["retrieval"]["top_k"]
    )
    
    generator = ResponseGenerator(
        model_name=config["models"]["llm"]["name"],
        max_tokens=config["models"]["llm"]["max_tokens"]
    )
    
    # Example query
    query = "What is the capital of Vietnam?"
    contexts = retriever.retrieve(query)
    response = generator.generate_response(query, contexts)
    
    logger.info(f"Query: {query}")
    logger.info(f"Response: {response}")

if __name__ == "__main__":
    main()
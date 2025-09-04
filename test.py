from src.rag_system import RAGSystem

# Truyền file config cụ thể
rag_system = RAGSystem(config_path="config.yaml")

while True:
    input_text = input("Enter a question (or 'exit' to quit): ")
    if input_text.lower() == 'exit':
        break
    answers = rag_system.query(input_text)
    print("Answers:", answers.get("response", ""))
    print("Retrieval Score:", answers.get("retrieval_score", "N/A"))

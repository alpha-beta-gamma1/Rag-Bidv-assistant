from src.rag_system import RAGSystem

rag_system = RAGSystem()
while   True:
    input_text = input("Enter a question (or 'exit' to quit): ")
    if input_text.lower() == 'exit':
        break
    answers = rag_system.query(input_text)
    print("Answers:", answers['response'])

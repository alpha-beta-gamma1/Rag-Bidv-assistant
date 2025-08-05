import os
import yaml
from pathlib import Path

def create_directory_structure():
    """Create the RAG project directory structure"""
    directories = [
        "data/raw/documents",
        "data/raw/web_scraping", 
        "data/raw/databases",
        "data/processed/chunks",
        "data/processed/embeddings",
        "data/external",
        "src/ingestion",
        "src/retrieval", 
        "src/generation",
        "src/evaluation",
        "src/utils",
        "notebooks",
        "tests",
        "configs",
        "scripts",
        "docker",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory.startswith("src/"):
            init_file = Path(directory) / "__init__.py"
            init_file.touch()
    
    print("✅ Directory structure created successfully!")

def create_config_files():
    """Create configuration files"""
    
    # Main config.yaml
    config = {
        'models': {
            'embedding_model': 'bkai-foundation-models/vietnamese-bi-encoder',
            'llm_model': 'Qwen/Qwen2.5-1.5B-Instruct',
            'device': 'cuda'  # Change to 'cpu' if no GPU
        },
        'chunking': {
            'max_tokens': 400,
            'overlap': 50
        },
        'retrieval': {
            'top_k': 3,
            'score_threshold': 0.6
        },
        'vector_store': {
            'type': 'faiss',
            'index_path': 'data/processed/embeddings/faiss_index',
            'dimension': 768
        },
        'generation': {
            'max_new_tokens': 512,
            'temperature': 0.7,
            'do_sample': True
        }
    }
    
    with open('configs/config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    # .env file
    env_content = """# Environment Variables for RAG System
CUDA_AVAILABLE=true
HF_TOKEN=your_huggingface_token_here
OPENAI_API_KEY=your_openai_key_here
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    # .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/raw/
data/processed/
*.faiss
*.chunks

# Logs
logs/
*.log

# Environment
.env
.env.local

# Model cache
.cache/
models/

# Jupyter
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ Configuration files created successfully!")

def create_requirements():
    """Create requirements.txt"""
    requirements = """# Core dependencies
torch>=2.0.0
transformers>=4.30.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4
numpy>=1.21.0
pandas>=1.5.0

# Document processing
python-docx>=0.8.11
PyPDF2>=3.0.0
openpyxl>=3.1.0

# Web and APIs
requests>=2.31.0
beautifulsoup4>=4.12.0

# Configuration and utilities
pyyaml>=6.0
python-dotenv>=1.0.0
tqdm>=4.65.0

# Evaluation
scikit-learn>=1.3.0
rouge-score>=0.1.2

# Development
jupyter>=1.0.0
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0

# Optional: For GPU support
# torch>=2.0.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html
# faiss-gpu>=1.7.4
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Requirements.txt created successfully!")

if __name__ == "__main__":
    create_directory_structure()
    create_config_files() 
    create_requirements()
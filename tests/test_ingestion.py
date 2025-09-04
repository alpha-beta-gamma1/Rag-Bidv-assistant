#!/usr/bin/env python3
import os
import sys
import json
import argparse
from glob import glob
from typing import List, Dict, Any

# add src to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.ingestion.embedder import Embedder
from src.retrieval.vector_store import VectorStore

logger = setup_logger(__name__)

def load_json_chunks(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def main():
    parser = argparse.ArgumentParser(
        description="Rebuild embeddings from JSON chunks and update FAISS index"
    )
    parser.add_argument(
        "--config",
        default="configs/config.yaml",
        help="Đường dẫn file config (mặc định: configs/config.yaml)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Xoá index/chunks cũ trước khi build lại (rebuild from scratch)",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Danh sách file/regex JSON chunks. Ví dụ: data/processed/chunks/*_chunks.json",
    )
    args = parser.parse_args()

    # Nếu không truyền inputs, dùng mặc định là file của em
    if not args.inputs:
        args.inputs = [
            r"D:\rag-project\data\processed\chunks\Thông tin Ngân hàng BIDV__chunks.json"
        ]

    # Resolve inputs (allow wildcards)
    files: List[str] = []
    for p in args.inputs:
        if any(ch in p for ch in ["*", "?", "["]):
            files.extend(glob(p))
        else:
            files.append(p)
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        logger.error("Không tìm thấy file JSON hợp lệ.")
        sys.exit(1)

    # Load config, embedder, vector store
    cfg = Config(args.config)
    embedder = Embedder(cfg)
    vs = VectorStore(cfg)

    # Optional reset: tạo index mới, xoá file cũ
    index_path = cfg.get("vector_store.index_path", "D:\\rag-project\\data\\processed\\embeddings\\faiss_index")
    if args.reset:
        vs._initialize_index()
        vs.chunks = []
        for ext in [".faiss", ".chunks"]:
            p = f"{index_path}{ext}"
            if os.path.exists(p):
                os.remove(p)
        logger.info("Đã reset vector store & xoá file index/chunks cũ.")

    # Cảnh báo mismatch dimension
    model_dim = embedder.dimension
    store_dim = vs.dimension
    if model_dim != store_dim:
        logger.error(
            f"dimension mismatch: embedder={model_dim} nhưng vector_store.dimension={store_dim}.\n"
            f"→ Sửa 'vector_store.dimension' trong {args.config} = {model_dim} rồi chạy lại."
        )
        sys.exit(2)

    total_added = 0
    for path in files:
        try:
            raw = load_json_chunks(path)
            chunks = embedder.validate_chunks(raw)
            if not chunks:
                logger.warning(f"{path}: Không có chunk hợp lệ, bỏ qua.")
                continue

            chunks_emb = embedder.embed_chunks(chunks)
            vs.add_chunks(chunks_emb)
            logger.info(f"{path}: +{len(chunks_emb)} chunks")
            total_added += len(chunks_emb)
        except Exception as e:
            logger.exception(f"Lỗi xử lý {path}: {e}")

    vs.save_index()
    stats = vs.get_stats()
    logger.info(
        f"Hoàn tất. Added={total_added}, total_chunks={stats['total_chunks']}, "
        f"index_size={stats['index_size']}, dim={stats['dimension']}"
    )
    print(
        f"✅ Done. Added {total_added} chunks. Total in store: {stats['total_chunks']} "
        f"(index_size={stats['index_size']}, dim={stats['dimension']})."
    )

if __name__ == "__main__":
    main()

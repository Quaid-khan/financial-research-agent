#!/usr/bin/env python3
"""Diagnostic script to check environment setup and dependencies.

Verifies:
1. Environment variables and .env file configuration.
2. SEC EDGAR User-Agent compliance.
3. Local Sentence-Transformers embedding model loading and inference.
4. ChromaDB persistent storage initialization and write test.
"""

import sys
import os
from pathlib import Path

# Add project root directory to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def print_header():
    print("=" * 65)
    print(" 🛠️  FINANCIAL RESEARCH AGENT - SYSTEM SETUP CHECK ")
    print("=" * 65)

def check_env_vars() -> bool:
    print("\n[1/4] Checking Environment Configuration...")
    env_file = project_root / ".env"
    if not env_file.exists():
        print("  ❌ FAIL: '.env' file not found in project root.")
        print("     Please copy '.env.example' to '.env' and populate your API keys.")
        return False
    print("  ✓ PASS: '.env' file exists.")

    try:
        from agent.config import get_settings
        settings = get_settings()
        print(f"  ✓ PASS: ANTHROPIC_API_KEY configured (starts with '{settings.anthropic_api_key[:7]}...')")
        print(f"  ✓ PASS: SEC_EDGAR_USER_AGENT valid ('{settings.sec_edgar_user_agent}')")
        return True
    except Exception as err:
        print(f"  ❌ FAIL: Configuration validation failed: {err}")
        return False

def check_embedding_model() -> bool:
    print("\n[2/4] Checking Sentence-Transformers Embedding Engine...")
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        print(f"  ... Loading model '{model_name}' (downloads on first run)...")
        model = SentenceTransformer(model_name)
        embedding = model.encode("Financial analysis 10-K query test.")
        print(f"  ✓ PASS: Model '{model_name}' loaded successfully. Vector dimension: {len(embedding)}")
        return True
    except Exception as err:
        print(f"  ❌ FAIL: Embedding model initialization failed: {err}")
        return False

def check_chroma_db() -> bool:
    print("\n[3/4] Checking ChromaDB Local Storage Write Access...")
    try:
        import chromadb
        db_path = os.getenv("CHROMA_DB_PATH", "./cache/chroma_db")
        abs_db_path = Path(db_path).resolve()
        abs_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(path=str(abs_db_path))
        test_collection = client.get_or_create_collection(name="setup_test_collection")
        test_collection.add(
            documents=["SEC EDGAR test filing snippet"],
            metadatas=[{"source": "setup_check"}],
            ids=["test_doc_1"]
        )
        results = test_collection.query(query_texts=["SEC EDGAR test"], n_results=1)
        client.delete_collection(name="setup_test_collection")
        print(f"  ✓ PASS: ChromaDB persistent client write & query verified at '{abs_db_path}'")
        return True
    except Exception as err:
        print(f"  ❌ FAIL: ChromaDB storage check failed: {err}")
        return False

def check_directories() -> bool:
    print("\n[4/4] Checking Required Directory Structure...")
    required_dirs = [
        "agent/tools", "agent/memory", "agent/synthesis",
        "agent/reporting", "eval/challenges", "tests", "examples", "cache"
    ]
    all_exist = True
    for d in required_dirs:
        p = project_root / d
        if p.exists() and p.is_dir():
            print(f"  ✓ PASS: Directory '{d}' exists.")
        else:
            print(f"  ❌ FAIL: Directory '{d}' missing.")
            all_exist = False
    return all_exist

def main():
    print_header()
    results = [
        ("Environment Variables", check_env_vars()),
        ("Embedding Model", check_embedding_model()),
        ("ChromaDB Vector Store", check_chroma_db()),
        ("Directory Structure", check_directories()),
    ]
    
    print("\n" + "=" * 65)
    print(" 📋 SUMMARY CHECKLIST")
    print("=" * 65)
    passed_count = 0
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} : {name}")
        if success:
            passed_count += 1
            
    print("-" * 65)
    if passed_count == len(results):
        print(" 🎉 SYSTEM READY: All environment and framework checks passed successfully!")
        sys.exit(0)
    else:
        print(f" ⚠️ ATTENTION: {len(results) - passed_count} check(s) failed. Please review errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

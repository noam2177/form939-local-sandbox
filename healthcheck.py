import os
import sys
import logging
from pathlib import Path
import asyncio

# Setup basic logging for the healthcheck
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HealthCheck")

def check_environment_variables():
    """Check if the .env file exists and warn if critical keys are missing."""
    logger.info("Checking environment variables...")
    if not Path(".env").exists():
        logger.warning("No .env file found. Cloud models will fail. Did you copy .env.example?")
        return False
    
    # We don't read the keys, just check if the file has content
    with open(".env", "r") as f:
        content = f.read()
        if "your_" in content:
            logger.warning(".env file contains placeholder values ('your_...'). Update them before using cloud models.")
            return False
    
    logger.info(".env file looks good.")
    return True

def check_directories():
    """Ensure required directories exist."""
    logger.info("Checking directory structure...")
    required_dirs = ["data/synthetic_inputs", "data/gold", "logs", "src"]
    all_good = True
    for d in required_dirs:
        if not Path(d).exists():
            logger.error(f"Missing required directory: {d}")
            all_good = False
    
    if all_good:
        logger.info("Directory structure is intact.")
    return all_good

async def check_ollama_connection():
    """Lightweight check to see if Ollama is running locally."""
    logger.info("Checking local Ollama connection...")
    try:
        import litellm
        # We do a tiny, fast request to see if the local server responds
        # Using a dummy model name just to see if the connection is refused or accepted
        # We expect a BadRequest or similar, but NOT a ConnectionError if it's running.
        try:
            await litellm.acompletion(
                model="ollama/llama3.1", 
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                timeout=15.0
            )
            logger.info("Ollama is running and responding.")
            return True
        except litellm.exceptions.APIConnectionError:
            logger.error("Ollama connection failed. Is the Ollama app running on your machine?")
            return False
        except Exception as e:
            # If it fails for another reason (like model not pulled), the server is at least up.
            logger.info(f"Ollama server is up (returned: {type(e).__name__}).")
            return True
    except ImportError:
        logger.error("litellm not installed.")
        return False

def main():
    print("=== Form939 Sandbox Health Check ===")
    env_ok = check_environment_variables()
    dirs_ok = check_directories()
    
    # Run async checks
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    ollama_ok = asyncio.run(check_ollama_connection())
    
    print("\n=== Summary ===")
    if not dirs_ok:
        print("[CRITICAL] Missing directories. Project structure is broken.")
        sys.exit(1)
        
    if not ollama_ok:
        print("[WARNING] Ollama is not running. Local models will fail.")
        
    if not env_ok:
        print("[WARNING] .env issues detected. Cloud models might fail.")
        
    if dirs_ok and ollama_ok and env_ok:
        print("[SUCCESS] All systems GO! You are ready to run the benchmark.")
    else:
        print("Review the warnings above before running the benchmark.")

if __name__ == "__main__":
    main()

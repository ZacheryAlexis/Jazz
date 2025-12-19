"""
Jazz - AI-powered CLI assistant
A fork of Ally (https://github.com/YassWorks/Ally)

Licensed under Apache License 2.0
See LICENSE and ATTRIBUTION.md for details
"""

import os, sys

# If running non-interactively (single-shot), set QUIET early so imports
# and agent/console initialization don't print banners. Look for flags in argv.
ARGS = " ".join(sys.argv[1:])
if "--once" in ARGS or "--json" in ARGS:
    os.environ["JAZZ_QUIET"] = "1"

from dotenv import load_dotenv
load_dotenv()

from app import CLI, default_ui

from warnings import filterwarnings
import os
import sys
import json
import logging


logging.basicConfig(level=logging.CRITICAL)
filterwarnings("ignore", category=Warning, module="torch")
filterwarnings("ignore", category=Warning, module="docling")
filterwarnings("ignore", category=Warning, module="huggingface_hub")


api_keys = {
    "cerebras": os.getenv("CEREBRAS_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "google": os.getenv("GOOGLE_GEN_AI_API_KEY"),
    "ollama": os.getenv("OLLAMA_API_KEY", "dummy")  
    
}


########### load the configuration ###########

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.json")
try:
    with open(config_path) as f:
        config = json.load(f)
    # Set Ollama URL env vars if present in config so downstream libs can connect
    if "ollama_host" in config:
        ollama_url = config["ollama_host"].rstrip("/")
        # Set several common env var names used by different clients
        os.environ["OLLAMA_HOST"] = ollama_url
        os.environ["OLLAMA_BASE_URL"] = ollama_url
        os.environ["OLLAMA_API_URL"] = ollama_url
except FileNotFoundError:
    default_ui.error("Configuration file 'config.json' not found.")
    sys.exit(1)
except json.JSONDecodeError:
    default_ui.error("Configuration file 'config.json' is not a valid JSON.")
    sys.exit(1)
except Exception as e:
    default_ui.error(f"An unexpected error occurred: {e}")
    sys.exit(1)


AGENT_TYPES = ["general", "code_gen", "brainstormer", "web_searcher"]


########### prepare the configuration ###########

provider = config.get("provider")
model = config.get("model")
api_key = api_keys.get(provider)

raw_provider_per_model = config.get("provider_per_model") or {}
provider_per_model = {k: (raw_provider_per_model.get(k) or provider) for k in AGENT_TYPES}

raw_models = config.get("models") or {}
models = {k: (raw_models.get(k) or model) for k in AGENT_TYPES}

api_key_per_model = {k: api_keys.get(provider_per_model.get(k), api_key) for k in AGENT_TYPES}

temperatures = config.get("temperatures") or {}
system_prompts = config.get("system_prompts") or {}

# If a concise prompt is provided via environment, prefer it for the 'general' agent
concise = os.getenv('JAZZ_CONCISE_PROMPT')
if concise and not system_prompts.get('general'):
    system_prompts['general'] = concise

embedding_provider = config.get("embedding_provider") or ""
embedding_model = config.get("embedding_model") or ""

scraping_method = config.get("scraping_method") or "simple"

client = CLI(
    provider=provider,
    provider_per_model=provider_per_model,
    models=models,
    api_key=api_key,
    api_key_per_model=api_key_per_model,
    embedding_provider=embedding_provider,
    embedding_model=embedding_model,
    temperatures=temperatures,
    system_prompts=system_prompts,
    scraping_method=scraping_method,
    stream=True,
)


########### run the CLI ###########

def main():
    args = sys.argv[1:]
    client.start_chat(*args)

if __name__ == "__main__":
    # Quick preflight: when running non-interactively with JSON output,
    # attempt a very fast one-sentence summary (no web lookups). If it
    # returns within a short timeout, print the JSON early so callers
    # (or the backend) can receive a concise answer immediately.
    try:
        if "--once" in ARGS and "--json" in ARGS:
            import threading

            # extract prompt passed via -p if present
            prompt = None
            try:
                if "-p" in sys.argv:
                    pi = sys.argv.index("-p")
                    if pi + 1 < len(sys.argv):
                        prompt = sys.argv[pi + 1]
                # backend may pass -p and the prompt as a single arg; else leave None
            except Exception:
                prompt = None

            if prompt:
                container = {"res": None, "meta": None}

                def _worker():
                    try:
                        pre_prompt = f"Answer in one short sentence WITHOUT web lookups: {prompt}"
                        # Try to temporarily avoid web research
                        prev_force = getattr(client.general_agent, 'force_research', None)
                        try:
                            setattr(client.general_agent, 'force_research', False)
                        except Exception:
                            prev_force = None
                        try:
                            r = client.general_agent.ask_once(pre_prompt, thread_id=None, active_dir=None, stream=False, return_meta=True)
                            if isinstance(r, (list, tuple)):
                                container['res'], container['meta'] = r[0], r[1]
                            else:
                                container['res'], container['meta'] = r, {"model": getattr(client.general_agent, 'model_name', None)}
                        finally:
                            try:
                                if prev_force is not None:
                                    setattr(client.general_agent, 'force_research', prev_force)
                            except Exception:
                                pass
                    except Exception:
                        pass

                t = threading.Thread(target=_worker, daemon=True)
                t.start()
                t.join(0.9)  # 900ms
                if not t.is_alive() and container.get('res'):
                    out = {
                        "response": container['res'],
                        "model": container['meta'].get('model') if container.get('meta') else getattr(client.general_agent, 'model_name', None),
                        "provider": container['meta'].get('provider') if container.get('meta') else getattr(client.general_agent, 'provider', None),
                        "duration_ms": container['meta'].get('duration_ms') if container.get('meta') else None,
                        "warnings": container.get('meta', {}).get('warnings', []),
                    }
                    try:
                        print(json.dumps(out, ensure_ascii=False))
                        sys.stdout.flush()
                    except Exception:
                        pass
    except Exception:
        pass

    main()

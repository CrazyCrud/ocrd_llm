# OCR-D extension to recognize text using open models via OpenAI interface 

> ocrd_llm is an OCR‑D module that tries to recognize text using open models via OpenAI interface. Currently tested with Academic Cloud.
       
_Disclaimer_: Work in progeress (maybe implement layout recognition in the future, too)

## Installation

```commandline
pip install .
```     

Or install via Docker:
```
- docker compose build
- docker-compose run ocrd-llm
```

## Quick Start

```commandline
ocrd-llm -I OCR-D-SEG-REGION-LINES -O OCR-D-SEG-REGION-LINES-RECOGNIZED-LLM --overwrite -p '{"model_id":"qwen3.5-35b-a3b", "api_endpoint": "", "api_key": ""}'
```

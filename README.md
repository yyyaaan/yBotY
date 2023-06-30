# yBotY

[![yBotY-app](https://github.com/yyyaaan/yBotY/actions/workflows/test-build-push-yBot.yaml/badge.svg)](https://github.com/yyyaaan/yBotY/actions/workflows/test-build-push-yBot.yaml)

> __yBotY__ is part of [__yyy-cluster__](https://github.com/yyyaaan/yyy-cluster/), and authentication is managed there.

Advance prompt engineering backend with API to LLM

Two set of APIs:
- sync API wait for all answers from LLM, often more structured
- streaming APIs sends token immediately one available, only in string


## Chat with Documents

```
from prompts.VectorStorage import VectorStorage
from prompts.DocumentQA import DocumentQA

# only-once: create Chroma DB for vector document
VectorStorage.chroma_create_persistent_db("/mnt/shared/file", "name")

# reuse the db and ask questions
agent = DocumentQA(db_name="name")
agent.ask("some question")
```
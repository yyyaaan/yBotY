# yBotY

[![yBotY-app](https://github.com/yyyaaan/yBotY/actions/workflows/test-build-push-yBot.yaml/badge.svg)](https://github.com/yyyaaan/yBotY/actions/workflows/test-build-push-yBot.yaml) 

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white) ![Vue.js](https://img.shields.io/badge/vuejs-%2335495e.svg?style=for-the-badge&logo=vuedotjs&logoColor=%234FC08D) ![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white) ![Swagger](https://img.shields.io/badge/-Swagger-%23Clojure?style=for-the-badge&logo=swagger&logoColor=white) ![Debian](https://img.shields.io/badge/Debian-D70A53?style=for-the-badge&logo=debian&logoColor=white) 



> __yBotY__ is part of [__yyy-cluster__](https://github.com/yyyaaan/yyy-cluster/), and authentication is managed there. See the last section below.

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

## Authentication from Parent App

This app is stateless, and thus has no user authentication. 

- Option 1: run this app in internal service, and proxy from parent app
- Option 2: mount the router in parent app, and inject dependencies

```
if exists("./app-bot/router.py"):
    from sys import path
    from app_bot.router import router
    from fastapi import Depends
    from auth.JWT import auth_user_token
    path.append("./app-bot")
    app.include_router(
        router=router,
        prefix="/bot",
        dependencies=[Depends(auth_user_token)]
    )
```

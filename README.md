---
title: career_assistant
app_file: app.py
sdk: gradio
sdk_version: 5.38.0
---
## 💬 Career Assistant Chatbot Project
This project is an intelligent career assistant chatbot that leverages structured data from my CV (in PDF format), a text-based professional summary, and public repositories from my GitHub profile to assist users in career-related discussions.

The chatbot is powered by function-calling tools and can dynamically interact with users using real-time data and responses. It supports three main tools:

### 🧠 Language Model (LLM)
The chatbot is built on `gemini-2.0-flash`, a lightweight and high-speed version of Google's Gemini large language model family. This version is optimized for fast inference and low latency, making it ideal for real-time chatbot interactions. It provides:
* Fast response generation
* Strong understanding of structured prompts
* Efficient tool-calling and reasoning
* Lower resource usage compared to heavier models
 
### 🔧 Implemented Tool
 
* 📌 `record_unknown_question`
If the chatbot is unable to answer a user's question, whether it's related to career or not, it triggers this tool to log the unknown question for further review and improvement.

* 📨 `record_user_details`
When a user engages in meaningful discussion, the assistant encourages them to provide their email address for further contact. This information is securely logged using this tool.

* 📂 `list_github_repos`
If a user asks about the projects I've worked on, this tool accesses my public GitHub repositories and returns a structured list containing:
    * Project Name
    * URL
    * Description<br>Each project is then described in bullet point format for clarity.

### 🔔 Smart Notifications
For real-time updates, both the `record_user_details` and `record_unknown_question` tools are integrated with Google Chrome push notifications, ensuring I receive alerts whenever:
    * A new user email is captured
    * A new unanswered question is recorded

## Project Setup

### UV Package Manager
UV is a modern, high-performance Python package manager and installer written in Rust. It serves as a drop-in replacement for traditional Python package management tools like pip, offering significant improvements in speed, reliability, and dependency resolution.
* Insall UV: follow instruction on this [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
* confirm the version: `uv --version`
* create virtual environment: `uv venv .venv`
* activate virtual environment (linux): `source .venv/Scripts/activate`
* On jupyter notebook, the virtual environment is name: `Python (myenv)`. Choose it to use the UV virtual environment on your notebook.
* Install required packages: `uv pip install -r requirements.txt`

### Setup Environment Variable
* Create `.env` in project root directory 
* Set up your API keys in the git ignore file

### Huggingface Deployment
Create a Dataset Repo
* huggingface-cli repo create about_me_bot_docs --type dataset
* Upload the data manualy or programmatically my going into the data repo created above

Login Huggingface on Terminal and Push all code to Space Repo
* Login huggingface on terminal: `huggingface-cli login`
* git remote add hf https://huggingface.co/spaces/O-G-O/AboutMe
* git push hf main


from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
import re 
from pypdf import PdfReader
import gradio as gr


load_dotenv(override=True)

def push(text):
    payload = {"token": os.getenv("PUSHOVER_TOKEN"),
               "user": os.getenv("PUSHOVER_USER"),
               "message": text
              }
    pushover_url = "https://api.pushover.net/1/messages.json"
    requests.post(pushover_url, data=payload)


def record_user_details(email, name="Name not provided", notes="not provided"):
    """
    Records user details and sends a push notification about the new entry.

    This function takes a user's email, optional name, and optional notes.
    It then sends a push notification (to my window chrome) summarizing
    the recorded interest. It's intended to be used in conjunction with information or a structure
    defined by `record_user_details_json`.

    Args:
        email (str): The email address of the user. This is a mandatory field.
        name (str, optional): The name of the user. Defaults to "Name not provided".
        notes (str, optional): Any additional notes or information about the user's interest.
                               Defaults to "not provided".

    Returns:
        dict: A dictionary indicating the status of the recording.
              Currently returns `{"recorded": "ok"}` regardless of actual storage.
    """
    # use information of record_user_details_json
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    """
    Records a user's question that the system was unable to answer and sends a push notification.

    This function takes a question string, sends a push notification
    to alert about the unanswerable question, and indicates that the question has been
    "recorded". It is intended to integrate the structure from `record_unknown_question_json` 
    for storage and logging.

    Args:
        question (str): The specific question that the system could not answer.

    Returns:
        dict: A dictionary indicating the status of the recording.
              Currently returns `{"recorded": "ok"}` regardless of actual storage.
    """
    # use information of record_unknown_question_json
    push(f"Recording {question} asked that I couldn't answer")
    return {"recorded": "ok"}


def list_github_repos(profile_url: str):
    """
    Lists all public repositories name, url and description
    
    Args:
        profile_url (str): GitHub profile URL.

    Returns:
        dict: A dictionary containing a list of public repository details if successful.
              Returns a dictionary with an "error" key if the username cannot be extracted,
              or the API request fails.
    """
    # 1. Extract username from the URL
    match = re.search(r'github\.com/([^/]+)', profile_url)
    username = match.group(1)
    
    base_api_url = f"https://api.github.com/users/{username}/repos"
    
    headers = {
        "Accept": "application/vnd.github.v3+json" 
    }
    
    all_repos = []
    page = 1
    per_page = 100 

    print(f"Attempting to list PUBLIC repositories for {username}...", flush=True)

    try:
        while True:
            params = {"page": page, "per_page": per_page, "type": "public"} 
            response = requests.get(base_api_url, headers=headers, params=params)
            response.raise_for_status() 

            repos_on_page = response.json()
            if not repos_on_page:
                break

            
            for repo in repos_on_page:
                if not repo.get("private"):
                    all_repos.append({
                        "name": repo.get("name"),
                        "html_url": repo.get("html_url"),
                        "description": repo.get("description"),
                    })

            # Check for 'Link' header to determine if there are more pages
            if 'link' not in response.headers or 'rel="next"' not in response.headers['link']:
                break # No more pages

            page += 1

        return {"repositories": all_repos, "count": len(all_repos)}
        
    except requests.exceptions.ConnectionError as errc:
        return {"error": f"Connection error fetching public repositories: {errc}. Check internet connection."}
    
    except requests.exceptions.Timeout as errt:
        return {"error": f"Timeout error fetching public repositories: {errt}. GitHub API took too long to respond."}
    
    except requests.exceptions.RequestException as err:
        return {"error": f"An unexpected error occurred during GitHub API request: {err}"}
    
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON response from GitHub API. Invalid API response."}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"]
    }
}

list_github_repos_json = {
    "name": "list_github_repos",
    "description": "Always use this tool to list all public repository names, URLs, and descriptions.",
    "parameters": {
        "type": "object", 
        "properties": {
            "profile_url": {
                "type": "string",
                "description": "The full GitHub profile URL (e.g. https://github.com/omogbolahan94)"
            }
        },
        "required": ["profile_url"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": list_github_repos_json}]


class Me:

    def __init__(self):
        # self.google_api_key = os.getenv('GEMINI_API_KEY')
        # self.google_gai_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.name = "Gabriel Olatunji"
        self.profiles = {'linkedin': '', 'resume': ''}

        for profile in self.profiles:
            reader = PdfReader(f"data-source/{profile}.pdf")
            result_str = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    result_str += text
            self.profiles[profile] += result_str
        self.linkedin = self.profiles['linkedin']
        self.resume = self.profiles['resume']
        
        with open("data-source/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()


    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    

    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
        particularly questions related to {self.name}'s career, background, skills and experience. \
        Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
        You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
        Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about         something trivial or unrelated to career. \
        If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool.\
        If the user requested to know about any projects you have worked on, use your list_github_repos tool to access your github repository and list repos with their names, url and description and then describe all relevant project in a well structured format even if it has to be in a bullet point format."
        
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        
        done = False
        while not done:
            # gemini = OpenAI(api_key=self.google_api_key, base_url=self.google_gai_url)
            # model_name = "gemini-2.0-flash"
            # response = gemini.chat.completions.create(model=model_name, messages=messages, tools=tools)
            # finish_reason = response.choices[0].finish_reason 
            openai_client = OpenAI(api_key=self.openai_api_key)

            model_name = "gpt-3.5-turbo"

            response = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools
            )
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_calls(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content


if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat, type="messages").launch()


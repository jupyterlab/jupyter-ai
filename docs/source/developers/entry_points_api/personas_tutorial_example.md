Based on the visual cues and discussions from the [Jupyter Zulip sprint](https://jupyter.zulipchat.com/#narrow/channel/531269-jupytercon/topic/.E2.9C.94.20jupyter-ai-sprint/with/558372308), here is a visual-led tutorial for setting up a local Ollama persona in Jupyter AI.

---

## 1. Initial Setup & Interface Check

Before coding, ensure you have the pre-release version of Jupyter AI (v3) installed, as this version supports the new persona architecture.

* **Install Command:**
```
pip install jupyterlab "jupyter_ai[all]" --pre
```
* **Verification:** Launch JupyterLab and open the chat panel. You should see an interface similar to the one shown in this screenshot.
![jupyter-ai v3](./docs/source/_static/jupyter-ai.png).
* **Test Chat:** Create a chat by clicking on `+ Chat`. Then try typing `@Jupyternaut hello` to ensure the base chat is working, even if no model is configured yet.
![jupyter-ai-chat](./docs/source/_static/jupyter-ai-chat-hello.png)
---

## 2. Create the Persona Directory

You need to create a specific hidden folder structure in your working directory for Jupyter AI to discover your custom personas.

* **Step:** Create the folder `.jupyter/personas/` in your project root. You need to create `.jupyter` folder first. Then go into the folder to create `personas` folder.
![folder structure screenshot](./docs/source/_static/jupyter-ai_personas_path.png)
* Enable showing hidden folder in File Browser in Settings
![show hidden folder](./docs/source/_static/enable_hidden_file.png)

```


```



---

## 3. Configure Ollama

* **Download:** Get Ollama from [ollama.com](https://ollama.com/download).
* **Model Selection:** Suggests using **gemma3:1b** as a lightweight local option.
* **Visual Reference:** Launch Ollama app. You can see the models and select one to download from the dropdown box showing in this 
![Ollama configuration screenshot](./docs/source/_static/jupyter-ai_ollama_model_selection.png)
* **Library:** Install the Python library from jupyter terminal 
```bash
pip install ollama
```

---

## 4. Implement the Persona Code

* Add a file `ollama_persona.py` to `/.jupyter/personas/` folder
* Add the following code to your `ollama_persona.py`

```python
from jupyter_ai_persona_manager import BasePersona, PersonaDefaults
from jupyterlab_chat.models import Message
from ollama import chat
import os

class OllamaPersona(BasePersona):
    @property
    def defaults(self):
        return PersonaDefaults(
            name="Ollama-Local",
            description="Local assistant via Ollama",
            system_prompt="You are a helpful local assistant.",
        )

    async def process_message(self, message: Message):
        # Call local Ollama API
        response = chat(
            model='gemma3:1b', #match to the downloaded model in previous step
            messages=[{'role': 'user', 'content': message.body}]
        )
        self.send_message(response['message']['content'])

```

> [!WARNING]
> **Avoid Infinite Loops:** Never echo the user's message back (e.g., `self.send_message(f"You said: {message.body}")`) as this can trigger an infinite loop that hangs JupyterLab.

---

## 5. Refresh and Activate

1. **Command:** In the Jupyter AI chat box, type `/refresh-personas`.
2. **Confirmation:** Once refreshed, your new persona should appear in the list of available personas when type in `@`, as shown in this 
![persona list screenshot](./docs/source/_static/jupyter-ai_ollama_persona.png)
3. **Chat:** Mention your new persona to start a local conversation: `@Ollama hello`
![ollama hello screenshot](./docs/source/_static/jupyter-ai_ollama_hello.png)

---

### Pro Tip: Adding Streaming

To make the text appear as it's generated (rather than waiting for the full block), use the `stream_message` method as demonstrated in the following
```python
# Getting started with Ollma


from jupyter_ai_persona_manager import BasePersona, PersonaDefaults
from jupyterlab_chat.models import Message
from ollama import chat
from ollama import ChatResponse
import os

# Path to avatar file in your package
AVATAR_PATH = os.path.join(os.path.dirname(__file__), "assets", "avatar.svg")


class MyLocalPersona(BasePersona):
    @property
    def defaults(self):
        return PersonaDefaults(
            name="ollama",
            description="A helpful custom assistant",
            avatar_path=AVATAR_PATH,  # Absolute path to avatar file
            system_prompt="You are a helpful assistant specialized in...",
        )

    async def process_message(self, message: Message):
        try:
            stream: Iterator[ChatResponse] = chat(
                model="gemma3:1b",
                messages=[{"role": "user", "content": message.body}],
                stream=True,
            )

            async def generate_content():
                for chunk in stream:
                    yield chunk["message"]["content"]

            await self.stream_message(generate_content())

        except Exception as e:
            self.send_message(f"Error: {e}")
```
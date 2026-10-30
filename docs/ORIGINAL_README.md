# Related Learning Materials

If you are looking for resources that will help you develop the skills required to complete this lab successfully, consider reviewing relevant sections from the following:

> [!NOTE]  
> The documentation links below may contain examples using Gemini API keys. For this lab, you must ignore those instructions and use the Agent Platform as detailed in the tasks below.

| Category | Resources |
| :--- | :--- |
| **Online Documentation** | [Agent Development Kit (ADK)](https://adk.dev/) <br> [Google Search Tool for ADK](https://adk.dev/integrations/google-search/) <br> [Structuring Data with ADK](https://adk.dev/schemas/) <br> [Sequential Agents](https://adk.dev/agents/) |
| **Courses, Labs, and Tutorials** | [Understand Google Cloud Agents](https://www.cloudskillsboost.google/) <br> [Build your first agent with Agent Development Kit (ADK)](https://www.cloudskillsboost.google/) <br> [Build intelligent agents with the Agent Development Kit (ADK)](https://www.cloudskillsboost.google/) |

---

# Challenge Scenario

You have just joined Cymbal Travel, a premier travel agency dedicated to curating the perfect vacation experiences for their customers. Cymbal Travel uses a suite of AI agents to scour the web for travel updates, validate destination data, and audit marketing brochures for accuracy.

![Cymbal Labs Logo](about:sanitized) *(Cymbal Labs Logo)*

Your team has built prototypes for a **"Travel Scout"** and a **"Brochure Auditor"** using Google's Agent Development Kit (ADK). However, the prototypes are currently misconfigured, incomplete, or broken.

*   The **Brochure Auditor** is supposed to be a multi-agent pipeline that both checks and fixes errors, but the previous engineer only implemented the "check" phase.
*   The **Travel Scout** hasn't been given access to Google Search yet.

As a new Agent Engineer, your job is to repair and deploy these agents to ensure downstream systems receive consistent, accurate data.

You will be working in the `adk_project` directory, which contains:
*   `my_google_search_agent`: A **"Travel Scout"** meant to search for events (currently broken).
*   `geo_validator`: A **"Destination Verifier"** that returns unstructured text (needs a strict schema).
*   `llm_auditor`: A sophisticated multi-agent system for brochure auditing (needs configuration).

### Your Challenge Tasks
1.  Initialize the Travel Scout (`my_google_search_agent`) to use the Google Search tool.
2.  Run the agent to find upcoming events.
3.  Enforce strict JSON schemas in the Destination Verifier (`geo_validator`).
4.  Configure the Brochure Auditor (`llm_auditor`) pipeline by enabling the missing Reviser Agent.

---

## Task 1. Install ADK and Set Up Your Environment

In this task, you will install the Agent Development Kit (ADK) and set up your environment.

1.  Open the **Cloud Shell Terminal**.
2.  Update your `PATH` environment variable and install ADK:

```bash
export PATH=$PATH:"/home/${USER}/.local/bin"
python3 -m pip install google-adk
```

3.  Authenticate to Google Cloud and set up application default credentials:

```bash
gcloud auth application-default login
```

4.  When prompted, type `Y`, and press **ENTER**.
5.  Click the authorization link in the terminal to launch the sign-in flow, log in with your lab student credentials, click **Allow**, and copy the verification code.
6.  Paste the authorization code into the terminal and press **ENTER**.
7.  Download and extract the source code for the lab:

```bash
gcloud storage cp gs://qwiklabs-gcp-04-92a9a1e91984-bucket/adk_project.zip .
unzip adk_project.zip
cd adk_project
pip install -r requirements.txt
```

---

## Task 2. Initialize and Configure the Travel Scout

### 1. Configure the Environment
Navigate to the directory `adk_project/my_google_search_agent`. Copy and paste the following configuration completely into `adk_project/my_google_search_agent/.env`:

```env
GOOGLE_GENAI_USE_ENTERPRISE=true
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-04-92a9a1e91984
GOOGLE_CLOUD_LOCATION=global
MODEL=gemini-3.5-flash
```

> [!NOTE]  
> Be sure to set `GOOGLE_CLOUD_LOCATION` to `global`. This is pertinent to the lab working successfully.

### 2. Update the Agent Code
Open `adk_project/my_google_search_agent/agent.py` and replace its entire contents with the following code to enable the Google Search tool:

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

agent = Agent(
    name="my_google_search_agent",
    description="An agent that searches the web using Google Search.",
    instruction="You are a helpful travel assistant. Always use Google Search to find real-time, accurate events and information.",
    tools=[google_search],
)
```

### 3. Launch the ADK Dev UI
From your Cloud Shell terminal, launch the web interface:

```bash
cd ~/adk_project
adk web --allow_origins "regex:https://.*\.cloudshell\.dev"
```

1.  Open the web interface URL provided in the terminal.
2.  Select **my_google_search_agent** and run the query:  
    > *"What are some major events in Tokyo in 2025?"*
3.  Stop the web server in the terminal using `CTRL+C`.

---

## Task 3. Verify the Agent via the CLI

Test your agent directly from the command-line interface:

```bash
# Run the agent in the CLI
adk run my_google_search_agent

# Ask the agent:
# "What is the currency exchange rate for Japan?"

# Press CTRL+C to exit when finished
```

---

## Task 4. Enforce Structured Standards

### 1. Configure the Environment
Navigate to `adk_project/geo_validator`. Copy and paste the following configuration completely into `adk_project/geo_validator/.env`:

```env
GOOGLE_GENAI_USE_ENTERPRISE=true
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-04-92a9a1e91984
GOOGLE_CLOUD_LOCATION=global
MODEL=gemini-3.5-flash
```

### 2. Update the Agent Code
Open `adk_project/geo_validator/agent.py` and replace its contents with the following code. This defines a strict Pydantic JSON schema and disables agent handoffs:

```python
from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.runners import Runner

# Define the structured output schema
class CountryCapital(BaseModel):
    capital: str = Field(description="The capital city of the requested country.")

agent = Agent(
    name="geo_validator",
    description="An agent that verifies geographic capital cities.",
    instruction="Return the capital city of the requested country in the strict JSON format specified.",
    output_schema=CountryCapital,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

if __name__ == "__main__":
    runner = Runner()
    response = runner.run(agent, "What is the capital of France?")
    print(response.text)
```

### 3. Run the Agent
Execute the script to verify that it prints a structured JSON object:

```bash
python3 geo_validator/agent.py
```

---

## Task 5. Deploy the Brochure Auditor

### 1. Configure the Environment
Navigate to `adk_project/llm_auditor`. Copy and paste the following configuration completely into `adk_project/llm_auditor/.env`:

```env
GOOGLE_GENAI_USE_ENTERPRISE=true
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-04-92a9a1e91984
GOOGLE_CLOUD_LOCATION=global
MODEL=gemini-3.5-flash
```

### 2. Update the Agent Code
Open `adk_project/llm_auditor/agent.py` and replace its contents with the following code. This un-comments the reviser import and adds it to the pipeline:

```python
from google.adk.agents import Agent
from .critic_agent.agent import agent as critic_agent
from .reviser_agent.agent import agent as reviser_agent

agent = Agent(
    name="llm_auditor",
    description="A multi-agent pipeline that fact-checks and revises brochures.",
    instruction="Audit the provided marketing claim. Use the Critic Agent to check for errors, and then have the Reviser Agent rewrite the claim based on those findings.",
    sub_agents=[critic_agent, reviser_agent],
)
```

### 3. Run and Audit the Claim
Launch the Dev UI again to verify the multi-agent orchestration pipeline:

```bash
cd ~/adk_project
adk web --allow_origins "regex:https://.*\.cloudshell\.dev"
```

1.  Select **llm_auditor** in the UI.
2.  Submit the claim:  
    > *"Double check this: You can take a direct train from Hawaii to Japan."*
3.  The pipeline should run the critic to identify the error, hand off to the reviser, and return the corrected factual claim.

from utils.InferenceProfile import InferenceProfile  # Adjust import path as needed
import json
import logging
import ollama
import anthropic
import openai

# --- Configuration ---
MODEL_NAME = "mistral-large:latest"  # Ollama model to use
OUTPUT_FILENAME = "synthetic_pen_test_data.jsonl"  # Output file for dataset
LOG_FILENAME = "pen_test_data_generation.log" # Log file for errors and info

# --- Logging Setup ---
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Data Variations (unchanged) ---
phases = [
    "Reconnaissance", "OSINT", "Network Mapping", "Vulnerability Scanning",
    "Exploitation", "Credential Attacks", "Lateral Movement", "Privilege Escalation",
    "Persistence", "Post-Exploitation", "Data Exfiltration", "Active Defense Evasion",
    "Social Engineering", "Web Application Testing", "Mobile Application Testing",
    "Cloud Security Testing", "Wireless Security Testing", "Physical Security Testing",
    "Red Team Operations", "Blue Team Simulation", "Incident Response Testing",
    "API Security Testing", "Hardware / IoT Security Testing", "Supply Chain Security Testing",
    "Reporting"
]

environments = [
    "Cloud (AWS)", "Cloud (Azure)", "Cloud (GCP)", "Internal Network", "External Network",
    "Wireless Networks", "Web Applications", "Mobile Applications", "Industrial Control Systems",
    "IoT Devices", "DevOps Environments", "Active Directory", "Containerized Environments",
    "Serverless Architectures", "Embedded Systems", "API Security", "Blockchain & Cryptocurrency",
    "Zero Trust Architectures", "AI/ML Workloads", "5G and Telecom Networks"
]

types = [
    "Black Box", "Gray Box", "White Box", "Red Team", "Purple Team", "Adversary Emulation",
    "Physical Penetration Testing", "Social Engineering", "Bug Bounty Testing", "Compliance Testing",
    "Threat Hunting Simulation", "Supply Chain Security Testing", "Active vs. Passive Testing",
    "Continuous Penetration Testing", "Cloud Red Teaming"
]

constraints = [
    "Stealth required", "Limited privileges", "Time-constrained", "Avoid service disruption",
    "Limited toolset", "Compliance restrictions", "Physical access required", "No internet connectivity",
    "Defender actively monitoring", "Covert exfiltration required", "EDR bypass needed", "Firewall restrictions",
    "Cloud-based only", "No shell access", "MFA enforced", "Security awareness testing", "Legacy systems involved",
    "Virtualized environments only", "AI-driven detections active", "Insider Threat Simulation"
]

# --- Prompt Templates ---
user_query_prompt_template = """
You are a penetration testing expert. Your task is to create a realistic user query that a penetration tester might ask.

Here's how to create the user query:

1. **Choose Context Variables:**  Mentally consider a penetration testing scenario by choosing ONE value for each of these context variables from the provided lists. You don't need to explicitly list these in the generated user query, but use them to inform the scenario:
    * Engagement Phase: Choose from: {phases}
    * Target Environment: Choose from: {environments}
    * Engagement Type: Choose from: {types}
    * Constraints: Choose from: {constraints}

2. **Generate a Realistic User Query:**  Based on the scenario you conceived using the context variables in step 1, write a realistic, natural language user query that a penetration tester would ask. The query should describe a specific penetration testing task they want to perform.  Think about:
    * **What is the pentester trying to achieve?** (e.g., identify vulnerabilities, exploit a service, gather information)
    * **Where are they operating?** (e.g., network type, specific system)
    * **What kind of output or result do they need?** (e.g., list of IPs, vulnerability report, file)

    **Example User Query:**
    ```
    I'm currently scanning an internal network and I need to check for SMBv1 signing enabled on live hosts. I want a file created that contains hostname, IP and SMB version information.
    ```

Respond ONLY with the user query, without any extra text or markdown formatting.
"""

response_prompt_template = """
You are a penetration testing expert. Your task is to respond to a penetration testing user query by generating a penetration testing command in JSON format.

Here's how to respond:

1. **Understand the User Query:** Carefully read and understand the provided user query.
2. **Respond to the User Query:** Generate a penetration testing command in JSON format that would address the user's request.

4. **JSON Output Format:** Your final response must be in JSON format and include the following:
    ```json
    {{
      "generated_user_query": "{user_query}",
      "command": "<generated_command>",
      "steps": {{
        "Goal Identification": "<Step 1: Clearly identify the goal of this specific command based on the user query.>",
        "Right Tool Selection": "<Step 2: Justify the selection of the tool(s) for this command and context.>",
        "Command Optimization": "<Step 3: Explain any specific options or parameters used to optimize the command for the user query's context.>",
        "Command Explanation": "<Step 4: Provide a concise explanation of what the command does and why it's appropriate for the user query.>",
        "Risk Analysis": "<Step 5: Briefly analyze potential risks associated with executing this command in the target environment (implied by the user query).>",
        "Risk Determination": "<Step 6: Determine and categorize the overall risk level (Low, Medium, High) of using this command in the implied context.>"
      }}
    }}
    ```

Ensure the generated command and steps are relevant to the **generated user query**. Focus on generating practical and realistic penetration testing commands that directly address the user's request. Respond ONLY in JSON format, without any extra text or markdown formatting outside the JSON block.
"""

def get_inference_profile_response(user_query, inference_profile):
    """Queries the model using the provided InferenceProfile and returns the raw response."""
    try:
        client = inference_profile.get_client()
        params = inference_profile.format_inference_params()

        messages = [{"role": "user", "content": user_query}]
        formatted_messages = inference_profile.format_messages_chat(messages)

        response = client.chat.completions.create(
            messages=formatted_messages,
            **params
        )
        return response
    except Exception as e:
        logging.error(f"InferenceProfile API call failed: {e}")
        return None

def get_ollama_response(user_query, model_name=MODEL_NAME):
    """Queries the Ollama model and returns the raw response."""
    try:
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": user_query}])
        return response
    except Exception as e:
        logging.error(f"Ollama API call failed: {e}")
        return None

def get_anthropic_response(user_query, model_name="claude-3-sonnet"):
    """Queries the Anthropic Claude model and returns the raw response."""
    try:
        client = anthropic.Client()
        response = client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": user_query}]
        )
        return response
    except Exception as e:
        logging.error(f"Anthropic API call failed: {e}")
        return None

def extract_json_content(response, original_user_query):
    """Extracts and parses JSON content from the response."""
    if not response:
        return None

    raw_content = response['message']['content']

    # Remove Markdown formatting (if any) - more robust removal
    if "```json" in raw_content:
        start_index = raw_content.find("`json") + len("`json")
        end_index = raw_content.find("```", start_index)
        if end_index != -1:
            raw_content = raw_content[start_index:end_index].strip()
        else:
            raw_content = raw_content[start_index:].strip() # In case of unclosed code block

    try:
        output = json.loads(raw_content)
        return output
    except json.JSONDecodeError as e:
        logging.error(f"JSONDecodeError: {e}. Raw content: {raw_content}")
        print(f"Invalid JSON response received. Check log file '{LOG_FILENAME}' for details.")
        return None

def generate_user_query():
    """Generates a realistic user query for penetration testing."""
    user_query_prompt = user_query_prompt_template.format(
        phases=", ".join(phases),
        environments=", ".join(environments),
        types=", ".join(types),
        constraints=", ".join(constraints)
    )

    response = get_ollama_response(user_query_prompt)
    if response:
        return response['message']['content']
    else:
        logging.warning(f"Failed to generate user query due to failed Ollama API call.")
        return None

def generate_response(user_query):
    """Generates a response to a penetration testing user query."""
    response_prompt = response_prompt_template.format(user_query=user_query)

    response = get_ollama_response(response_prompt)
    if response:
        output = extract_json_content(response, user_query)
        if output:
            return output
        else:
            logging.warning(f"Skipping response due to invalid JSON output.")
    else:
        logging.warning(f"Skipping response due to failed Ollama API call.")
    return None

def generate_penetration_testing_data(user_query=None):
    """Generates penetration testing data, either from a provided user query or a newly generated one."""
    if not user_query:
        user_query = generate_user_query()
        if not user_query:
            return None

    response = generate_response(user_query)
    if response:
        response['generated_user_query'] = user_query
        return response
    else:
        return None

def save_dataset_to_jsonl(dataset, filename=OUTPUT_FILENAME):
    """Saves the generated dataset to a JSONL file."""
    try:
        with open(filename, "a+") as f: # Use 'a+' to append or create
            for obj in dataset:
                f.write(json.dumps(obj) + "\n")
        print(f"Dataset saved successfully to '{filename}'!")
        logging.info(f"Dataset saved successfully to '{filename}'. Total samples: {len(dataset)}")
    except Exception as e:
        logging.error(f"Error saving dataset to file: {e}")
        print(f"Error saving dataset. Check log file '{LOG_FILENAME}' for details.")

if __name__ == "__main__":
    # Add command line argument parsing
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic penetration testing command data")
    parser.add_argument("--use-profile", action="store_true", help="Use InferenceProfile instead of Ollama")
    parser.add_argument("--size", type=int, default=1, help="Number of samples to generate (default: 1)")
    parser.add_argument("--output", type=str, default=OUTPUT_FILENAME, help=f"Output file name (default: {OUTPUT_FILENAME})")
    args = parser.parse_args()

    dataset = []
    for _ in range(args.size):
        data = generate_penetration_testing_data()
        if data:
            dataset.append(data)
        else:
            logging.warning(f"Skipping sample due to failed data generation.")

    if dataset:
        save_dataset_to_jsonl(dataset, filename=args.output)
    else:
        print("Dataset generation failed. Check log file for errors.")
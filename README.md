
---

# Penetration Testing Command Generator & Slack Bot  

A system for **generating penetration testing scenarios** and **automating Slack interactions** to support dataset curation.  

---

## Files Overview  
- **`slack_bot.py`**: A Slack bot for sending reminders and generating penetration testing queries via the `/query` command.  
- **`generate.py`**: A script to **generate synthetic penetration testing data** (user queries + commands) using LLMs like Ollama or Anthropic.  
- **`.env`**: Configuration file storing **Slack API tokens**, environment variables, and paths to model directories.  

---

## Installation & Setup  

### 1. **Install Dependencies**  
Install required Python packages:  
```bash  
pip install -r requirements.txt
```  

### 2. **Configure `.env`**  
Create a `.env` file and update the following variables with your own credentials:  
```env  
# Slack API tokens (required)  
SLACK_APP_TOKEN="your-app-token"  
SLACK_BOT_TOKEN="your-bot-token"  
SLACK_SIGNING="your-signing-secret"  

# Paths to directories (adjust as needed)  
PROFILES_DIR="/path/to/profiles/directory"  
```  

---

## Usage  

### 1. **Run the Slack Bot**  
Start the bot to handle user interactions and scheduled reminders:  
```bash  
python slack_bot.py  
```  

**Features**:  
- **Morning Reminders**: Daily at 9:00 AM, all active users receive a `/query` reminder.  
- **`/query` Command**:  
  - Generates penetration testing scenarios (e.g., "Need to exploit a misconfigured S3 bucket").  
  - Example usage:  
    ```bash  
    /query -c 3  # Generate 3 scenarios  
    ```  

### 2. **Generate Synthetic Penetration Testing Data**  
Use `generate.py` to create datasets for training or testing:  
```bash  
python generate.py --size 100 --output my_dataset.jsonl  
```  

**Options**:  
- `--size`: Number of samples to generate (default=1).  
- `--output`: Output file name (default=`synthetic_pen_test_data.jsonl`).  
- `--use-profile`: Use an `InferenceProfile` (e.g., for custom models) instead of Ollama.  

---

## Configuration Details  

### **Slack Bot**  
- **Scheduled Reminders**: The bot runs `send_morning_reminder()` daily at 9:00 AM.  
- **User Management**: Uses `app.client.users_list()` to fetch active users (excluding bots and deactivated accounts).  

### **Data Generation (`generate.py`)**  
- **Models Supported**:  
  - Ollama (default, via `MODEL_NAME="mistral-large:latest"`).  
  - Anthropic Claude (`claude-3-sonnet`).  
  - OpenAI (if configured).  
- **Context Variables**:  
  Scenarios are generated using predefined lists of:  
  - Phases (e.g., "Post-Exploitation").  
  - Environments (e.g., "Cloud (AWS)").  
  - Engagement types (e.g., "Red Team").  
  - Constraints (e.g., "Stealth required").  

---

## Example Workflow  

1. **Generate a dataset**:  
   ```bash  
   python generate.py --size 50 --output test_dataset.jsonl  
   ```  

2. **Run the Slack bot**:  
   ```bash  
   python slack_bot.py  
   ```  
   Users can then use `/query` to get real-time scenarios or receive daily reminders.  

---

## Important Notes  

- **Ethical Use**: This tool is for **authorized penetration testing**. Do not use it for unauthorized activities.  
- **API Limits**: Respect Slack’s API rate limits and LLM provider quotas.  
- **Error Handling**: Check logs (`pen_test_data_generation.log`) for errors during data generation.  

--- 

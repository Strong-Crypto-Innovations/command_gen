from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
import re
from dotenv import load_dotenv
from generate import generate_user_query
from datetime import datetime
import time
import threading
import schedule

# Load environment variables from a .env file
load_dotenv()

# Initialize the Bolt app with your Slack bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING")
)

# Get OpenWebUI chat URL from environment variables or use a default
OPENWEBUI_CHAT_URL = os.environ.get("OPENWEBUI_CHAT_URL", "http://100.65.0.99:3000/")

def get_all_users():
    """Get all users in the workspace"""
    try:
        response = app.client.users_list()
        # Filter out bots, slackbot, and deactivated accounts
        active_users = {
            member["name"]: member["id"] for member in response["members"]
            if not member.get("is_bot", False) and
               member.get("id") != "USLACKBOT" and
               not member.get("deleted", False)
        }
        return active_users
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return []

def send_morning_reminder():
    """
    Sends a morning reminder to individual users to perform penetration testing queries.
    This will be sent as a direct message to each user every morning.
    """
    # Get list of user IDs to send reminders to (from environment variable)
    user_ids_lst = [user_id for user_id in get_all_users().values()]
    
    # Current date for the message
    today = datetime.now().strftime("%A, %B %d, %Y")
    
    # Create reminder message
    reminder_text = (
        f"☀️ *Good Morning!* | {today}\n\n"
        f"*Daily Reminder*: Help curate our command dataset today by using the `/query` command.\n\n"
        f"*Try these options*:\n"
        f"• Basic scenario: `/query`\n"
        f"• Multiple scenarios: `/query -c 3`\n\n"
        f"_Generate scenarios and paste them into <{OPENWEBUI_CHAT_URL}|OpenWebUI Chat> to help grow our high quality dataset!_\n\n"
    )
    
    # Send the reminder to each user
    for user_id in user_ids_lst:
        try:
            # Open a DM channel with the user
            response = app.client.conversations_open(users=[user_id])
            dm_channel = response["channel"]["id"]
            
            # Send message to the DM channel
            app.client.chat_postMessage(
                channel=dm_channel,
                text=reminder_text
            )
            print(f"[{datetime.now()}] Reminder sent to user {user_id}")
        except Exception as e:
            print(f"[{datetime.now()}] Error sending reminder to user {user_id}: {str(e)}")

# Function to run the scheduler in a separate thread
def run_scheduler():
    """Run the scheduler in a background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Setup the scheduler to run the reminder at 9:00 AM every day
def setup_scheduler():
    # Schedule the reminder for 9:00 AM every day
    schedule.every().day.at("09:00").do(send_morning_reminder)
    
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("📅 Daily reminder scheduler initialized!")


# Handle the /query command
@app.command("/query")
def handle_query_command(ack, say, command, client, body):
    # Acknowledge the command request immediately
    ack({"text": "Request received! Working on your penetration testing scenario..."})

    # Parse the command to extract the count
    text = command.get("text", "")
    count = 1  # Default count

    # Use regex to find -c flag followed by a number
    count_match = re.search(r'-c\s+(\d+)', text)
    if count_match:
        count = int(count_match.group(1))
        # Limit the count to prevent abuse
        count = min(count, 5)  # Maximum of 5 scenarios

    # Open a DM channel with the user
    response = client.conversations_open(users=[command["user_id"]])
    dm_channel = response["channel"]["id"]
    
    # Send an initial "thinking" message
    thinking_message = client.chat_postMessage(
        channel=dm_channel,
        text="🔍 *Processing Request*: Generating a random contextual penetration testing scenario for you. This might take a moment...",
        thread_ts=command.get("thread_ts")
    )

    try:
        
        # Generate multiple scenarios if requested
        scenarios = []
        for i in range(count):
            # Add progress updates for multiple scenarios
            if count > 1 and i > 0:
                client.chat_update(
                    channel=thinking_message["channel"],
                    ts=thinking_message["ts"],
                    text=f"🧠 *Analyzing*: Creating scenario {i+1} of {count}..."
                )
            
            user_query = generate_user_query()
            if user_query:
                scenarios.append(user_query)

        # Update with final result
        if scenarios:
            # Format multiple scenarios with numbering
            formatted_scenarios = ""
            for i, scenario in enumerate(scenarios, 1):
                formatted_scenarios += f"*Scenario {i}*:\n```{scenario}```\n\n"
            
            client.chat_update(
                channel=thinking_message["channel"],
                ts=thinking_message["ts"],
                text=f"✅ *Generated {len(scenarios)} Scenario(s)*:\n\n{formatted_scenarios}_Copy and paste these scenarios to <{OPENWEBUI_CHAT_URL}|OpenWebUI Chat> to get started!_"
            )
        else:
            client.chat_update(
                channel=thinking_message["channel"],
                ts=thinking_message["ts"],
                text="❌ *Generation Failed*: Sorry, I couldn't generate any penetration testing scenarios. Please try again or check the system logs for details."
            )
    except Exception as e:
        # Handle any errors during the process
        client.chat_update(
            channel=thinking_message["channel"],
            ts=thinking_message["ts"],
            text=f"⚠️ *Error*: Something went wrong while generating your scenario: {str(e)}"
        )

# Start the app
if __name__ == "__main__":
    setup_scheduler()
    # Start the app using Socket Mode
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    print("⚡️ Slack bot is running!")
    handler.start()
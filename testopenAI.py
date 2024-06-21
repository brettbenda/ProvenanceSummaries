from dotenv import load_dotenv # Keeping API secrets 
import os # To move through the file tree to get to the .env file with the API Key
from openai import OpenAI # Connect to LLM

load_dotenv()

def summarize_logs(interaction_logs):
    try:
        # Create a prompt that asks the model to summarize the logs
        prompt = f"Summarize the following interaction logs:\n\n{interaction_logs}\n\nSummary:"

        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
            max_tokens=150,  # Adjust based on the desired summary length
            temperature=0.5,  # Adjust for summary precision
        )

        return chat_completion.choices[0].message.content
    except Exception as e:
        return str(e)

# Example usage
if __name__ == "__main__":
    interaction_logs = """
    User: Hi, I need help with my account.
    Assistant: Sure, I'd be happy to help. What seems to be the issue?
    User: I can't log in.
    Assistant: Have you tried resetting your password?
    User: Yes, but I didn't receive the reset email.
    Assistant: Can you please check your spam folder?
    User: I checked, and it's not there.
    Assistant: Let me check our system. Can I have your email address?
    User: It's user@example.com.
    Assistant: Thank you. It appears there was a typo in the email address we have on file. I'll correct it and send you another reset email.
    User: Got it, thanks!
    Assistant: You're welcome! Is there anything else I can help you with?
    User: No, that's all.
    """
    
    summary = summarize_logs(interaction_logs)
    print("Summary:", summary)

from openai import OpenAI

client = OpenAI(api_key="sk-b7550aa67ed840ffacb5ca051733802c", base_url="https://api.deepseek.com")

def handle_conversation():
    # Initialize messages list for the conversation
    messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
    
    # Round 1
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
        stream=True
    )

    reasoning_content = ""
    content = ""

    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
            reasoning_content += chunk.choices[0].delta.reasoning_content
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content

    # Store the assistant's response
    messages.append({"role": "assistant", "content": content})
    
    # Round 2 - User's follow-up question
    messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
    
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
        stream=True
    )

    # Reset content variables for the second round
    reasoning_content = ""
    content = ""

    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
            reasoning_content += chunk.choices[0].delta.reasoning_content
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content

    # Return the final assistant response
    return reasoning_content

# Example usage
if __name__ == "__main__":
    final_response = handle_conversation()
    print("Final assistant response:", final_response)
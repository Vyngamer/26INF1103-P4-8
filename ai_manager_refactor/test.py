from ai_manager_refactor import AICounsellor

print("\nLoading...\n")

client = AICounsellor()

client.connect_client()

conversation_start = client.call_api("Hello!")

print(conversation_start)
print()

while True:
    prompt = input("Enter prompt:\n")

    chat_response = client.call_api(prompt).data

    print(chat_response)


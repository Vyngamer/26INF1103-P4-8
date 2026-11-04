from ai_manager_refactor import AICounsellor

print("\nLoading...\n")

client = AICounsellor()

try:
    client_connection = client.connect_client()
except Exception as e:
    print(e)
    print("Terminating program")
    exit()

conversation_start = client.call_api("Hello!")

print(conversation_start)
print()

while True:
    prompt = input("Enter prompt:\n")

    chat_response = client.call_api(prompt).data

    print(chat_response)


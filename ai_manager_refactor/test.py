from ai_manager_refactor import AICounsellor, EntityExtraction

print("\nLoading...\n")

client = AICounsellor()
entity_extraction = EntityExtraction()

client.connect_client()
entity_extraction.connect_client()

print(client.call_api("Hello!"))

s = ''
while True:
    prompt = input("Enter prompt:\n\t")
    s = s + prompt + '\n'

    print("\nLoading response...\n")

    json_response = entity_extraction.call_api(s).data
    s = s + json_response + '\n'
    
    print(json_response)
    print()
    
    chat_response = client.call_api(prompt).data
    s = s + chat_response + '\n'

    print(chat_response)

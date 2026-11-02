from ai_manager_refactor import GeminiClient

model = "gemini-3.1-flash-lite" 
system_instruction = ""

client = GeminiClient(model, system_instruction)

print(client.connect_client())

# print(client.call_api("Hello!"))

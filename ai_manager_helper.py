from google import genai
from io_manager import print_error, print_notice
import sys
import os
import json
import google
from google.genai._gaos.lib.compat_errors import APIConnectionError, NotFoundError


# decorator which handles general errors after all other error handlers
def general_error_handler(base_api_call_func):
    def catch_general_error(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)
        except Exception as e:
            print_error("No AI functionality.")
            raise e

    return catch_general_error

# decorator to handle other errors
def backup_model_retry(base_api_call_func):
    def retry_api_call(*args, **kwargs):
        try: 
            return base_api_call_func(*args, **kwargs)
        except NotFoundError as e:
            print_error("An error occured.")
            print_notice("Retrying with secondary model...")

            try:
                kwargs['model'] = backup_model
                return base_api_call_func(*args, **kwargs)
            except NotFoundError as e: 
                print_error("Both models unavailable.")
                raise e
    
    return retry_api_call

# decorator to handle network failure
def failed_network_handler(base_api_call_func):
    def failed_network_notice(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)
        except APIConnectionError as e:

            print_error("Network connection error. Please check that you are connected to the internet.")
            raise e
    return failed_network_notice

# decorator for when the primary api key fails
def failed_api_key_handler(base_api_call_func):
    def api_key_fallback(*args, **kwargs):
        try:
            return base_api_call_func(*args, **kwargs)    
        except ValueError as e:
            print_error("Primary key failed... Switching to alternate key")
            
            os.environ["GEMINI_API_KEY"] = os.getenv("BACKUP_GEMINI_API_KEY")
            try:
                return base_api_call_func(*args, **kwargs) 
            except ValueError as e:
                print_error("Both API keys unavailable...")
                raise e
        
    return api_key_fallback


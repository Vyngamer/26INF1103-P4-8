from abc import ABC, abstractmethod

class ICounsellingStrategy(ABC):
    @abstractmethod
    def get_system_instruction(self) -> str:
        pass
    
    @abstractmethod
    def get_json_response_schema(self) -> dict:
        pass


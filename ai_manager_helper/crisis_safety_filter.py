import re

class CrisisDetectedError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class CrisisSafetyFilter:
    CRISIS_KEYWORDS = [
        r"suicide", r"kill myself", r"end it all", r"want to die", 
        r"self[-\s]harm", r"hurt myself"
    ]

    def validate(self, text: str) -> None:
        text_lower = text.lower()
        for pattern in self.CRISIS_KEYWORDS:
            if re.search(pattern, text_lower):
                raise CrisisDetectedError("Crisis Detected")


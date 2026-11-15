import re

class CrisisSafetyFilter:
    CRISIS_KEYWORDS = [
        r"suicide", r"kill myself", r"end it all", r"want to die", 
        r"self[-\s]harm", r"hurt myself"
    ]

    def validate(self, text: str) -> None:
        text_lower = text.lower()
        for pattern in self.CRISIS_KEYWORDS:
            if re.search(pattern, text_lower):
                raise Exception("Crisis Detected")


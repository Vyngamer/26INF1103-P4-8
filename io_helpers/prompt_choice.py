'''
Choice Prompt (Child of RangePrompt)
'''

from io_helpers.prompt_range import RangePrompt
from io_helpers.errors.invalid_input import InvalidInput

# One answer from a list of options
# Returns the chosen option
# Inherits number parsing / range checking from RangePrompt
class ChoicePrompt(RangePrompt):
    def __init__(self, options):
        options = list(options)
        if not options:     # Rejects an empty list of options
            raise ValueError("ChoicePrompt needs at least one option.")
        super().__init__(1, len(options))
        self.options = options
        # Msg for an answer that is neither one of the options nor its number
        self.choose_msg = "Please choose one of: " + ", ".join(str(option) for option in options) + "."

    # Accepts the option itself in any letter case (e.g. "calm" from chatbot)
    # or its number (1 = first option). Returns the option as written in options
    def parse(self, raw):
        text = self.clean(raw)
        for option in self.options:
            if text.lower() == str(option).lower():
                return option
        try:
            return self.options[super().parse(text) - 1]
        except InvalidInput:
            raise InvalidInput(self.choose_msg) from None
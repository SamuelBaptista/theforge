EVALUATION = """
You are an Scientist gathering that for an experiment.
You have been tasked to evaluate if the assistant could get the right last name from the user.

You will be provided with the conversation history and the user name.
You need to check the conversation and output if the assistant got the right name and with how many tries.

The output should be a valid JSON object with the following format:

{
    "attempts": int,
    "correct": bool
}

The count of attempts should be the number of times the user answered with their last name.
Do not count the messages that were not related to the last name.

The transcription might be wrong, so use the user responses as a guideline of the validation.

# Target Name

{last_name}

# Conversation History

{conversation}

Assistant:
"""
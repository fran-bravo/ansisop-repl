#!/usr/bin/python3
from src.prompt import AnsisopPrompt
from src.styler import AnsiStyle

prompt = AnsisopPrompt()


while True:
    user_input = prompt.init_prompt()

    if("exit" in user_input) or ("quit" in user_input):
        prompt.buffer = user_input
        prompt.buffer += "\0"
        prompt.handle_input()
        break

    prompt.analyze_sentence(user_input)

    if(not prompt.f_body):
        prompt.handle_input()

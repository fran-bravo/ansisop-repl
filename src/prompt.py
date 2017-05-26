from .completer import AnsisopCompleter, AnsisopKeywords
from .connection import Connection
from .lexer import AnsisopLexer
from prompt_toolkit import prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.token import Token

from src.styler import AnsiStyle


def continuation_tokens(cli, width):
    " The continuation: display dots before all the following lines. "

    # (make sure that the width of the continuation does not exceed the given
    # width. -- It is the prompt that decides the width of the left margin.)
    return [(Token, '.' * (width - 1) + ' ')]


class AnsisopPrompt(object):

    def __init__(self):
        self.keywords = AnsisopKeywords
        self.msg = 'ars>'
        self.completer = AnsisopCompleter()
        self.lexer = AnsisopLexer
        self.style = AnsiStyle
        self.f_body = False
        self.buffer = ""
        self.connection = Connection("src/config.cfg")
        self.connection.connect()

    def init_prompt(self):
        return prompt(message=self.msg,
                history=FileHistory('history.txt'),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                lexer=self.lexer,
                style=self.style,
                multiline=False,
                get_continuation_tokens=continuation_tokens,
                )

    def validate_sentence(self, sentence):
        pass

    def analyze_sentence(self, sentence):
        if("function" in sentence):
            self._function_buffer(sentence)
        elif(self.f_body and "end" in sentence):
            self._function_end_buffer(sentence)
        elif(self.f_body):
            self.buffer += sentence
            self.buffer += "\n"
        else:
            self.buffer = sentence
            self.buffer += "\0"

    def handle_input(self):
        self.connection.send(self.buffer)
        #TODO: recibir codigo compilado/ejecutado y mostrar el resultado

    def _function_buffer(self, sentence):
        self.f_body = True
        self.buffer = ""
        self.buffer += sentence
        self.buffer += "\n"
        self._continuation_message()

    def _function_end_buffer(self, sentence):
        self.f_body = False
        self.buffer += sentence
        self.buffer += "\0"
        self._normal_message()

    def _continuation_message(self):
        self.msg = '... '

    def _normal_message(self):
        self.msg = 'ars>'

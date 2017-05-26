from prompt_toolkit.completion import Completer, Completion
from fuzzyfinder import fuzzyfinder

AnsisopKeywords = ['begin', 'end', 'function', 'variables', 'goto', 'jnz', 'jz',
                   'return', 'io', 'wait', 'signal', 'alocar', 'liberar',
                   'abrir', 'borrar', 'cerrar', 'buscar', 'escribir', 'leer',
                   'exit', 'quit']


class AnsisopCompleter(Completer):
    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        matches = fuzzyfinder(word_before_cursor, AnsisopKeywords)
        for m in matches:
            yield Completion(m, start_position=-len(word_before_cursor))

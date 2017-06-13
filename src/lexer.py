# -*- coding: utf-8 -*-
"""
    ~~~~~~~~~~~~~~~~~~~~

    Lexers for Ansisop and related languages.


"""

import re

from pygments.lexer import Lexer, RegexLexer, ExtendedRegexLexer, include, \
    bygroups, default, LexerContext, do_insertions, words
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Error, Generic
from pygments.util import shebang_matches

__all__ = ['AnsisopLexer', 'AnsisopConsoleLexer']

line_re = re.compile('.*?\n')


ANSISOP_OPERATORS = (
    '*', '-', '+', '/', '&', '<-', '<', '<=', '>', '>=', '==', ':'
)


class AnsisopLexer(ExtendedRegexLexer):
    name = 'Ansisop'
    aliases = ['asop', 'ansisop']
    filenames = ['*.asop', '*.ansisop']
    mimetypes = ['text/x-ansisop', 'application/x-ansisop']

    flags = re.DOTALL | re.MULTILINE

    def gen_ansisopstrings_rules():
        def intp_regex_callback(self, match, ctx):
            yield match.start(1), String.Regex, match.group(1)  # begin
            nctx = LexerContext(match.group(3), 0, ['interpolated-regex'])
            for i, t, v in self.get_tokens_unprocessed(context=nctx):
                yield match.start(3)+i, t, v
            yield match.start(4), String.Regex, match.group(4)  # end[mixounse]*
            ctx.pos = match.end()

        def intp_string_callback(self, match, ctx):
            yield match.start(1), String.Other, match.group(1)
            nctx = LexerContext(match.group(3), 0, ['interpolated-string'])
            for i, t, v in self.get_tokens_unprocessed(context=nctx):
                yield match.start(3)+i, t, v
            yield match.start(4), String.Other, match.group(4)  # end
            ctx.pos = match.end()

        states = {}
        states['strings'] = [
            # easy ones
            (r'\:@{0,2}[a-zA-Z_]\w*[!?]?', String.Symbol),
            (words(ANSISOP_OPERATORS, prefix=r'\:@{0,2}'), String.Symbol),
            (r":'(\\\\|\\'|[^'])*'", String.Symbol),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r':"', String.Symbol, 'simple-sym'),
            (r'([a-zA-Z_]\w*)(:)(?!:)',
             bygroups(String.Symbol, Punctuation)),  # Since Ruby 1.9
            (r'"', String.Double, 'simple-string'),
            (r'(?<!\.)`', String.Backtick, 'simple-backtick'),
        ]

        # double-quoted string and symbol
        for name, ttype, end in ('string', String.Double, '"'), \
                                ('sym', String.Symbol, '"'), \
                                ('backtick', String.Backtick, '`'):
            states['simple-'+name] = [
                include('string-intp-escaped'),
                (r'[^\\%s#]+' % end, ttype),
                (r'[\\#]', ttype),
                (end, ttype, '#pop'),
            ]

        # braced quoted strings
        for lbrace, rbrace, bracecc, name in \
                ('\\{', '\\}', '{}', 'cb'), \
                ('\\[', '\\]', '\\[\\]', 'sb'), \
                ('\\(', '\\)', '()', 'pa'), \
                ('<', '>', '<>', 'ab'):
            states[name+'-intp-string'] = [
                (r'\\[\\' + bracecc + ']', String.Other),
                (lbrace, String.Other, '#push'),
                (rbrace, String.Other, '#pop'),
                include('string-intp-escaped'),
                (r'[\\#' + bracecc + ']', String.Other),
                (r'[^\\#' + bracecc + ']+', String.Other),
            ]
            states['strings'].append((r'%[QWx]?' + lbrace, String.Other,
                                      name+'-intp-string'))
            states[name+'-string'] = [
                (r'\\[\\' + bracecc + ']', String.Other),
                (lbrace, String.Other, '#push'),
                (rbrace, String.Other, '#pop'),
                (r'[\\#' + bracecc + ']', String.Other),
                (r'[^\\#' + bracecc + ']+', String.Other),
            ]
            states['strings'].append((r'%[qsw]' + lbrace, String.Other,
                                      name+'-string'))
            states[name+'-regex'] = [
                (r'\\[\\' + bracecc + ']', String.Regex),
                (lbrace, String.Regex, '#push'),
                (rbrace + '[mixounse]*', String.Regex, '#pop'),
                include('string-intp'),
                (r'[\\#' + bracecc + ']', String.Regex),
                (r'[^\\#' + bracecc + ']+', String.Regex),
            ]
            states['strings'].append((r'%r' + lbrace, String.Regex,
                                      name+'-regex'))

        # these must come after %<brace>!
        states['strings'] += [
            # %r regex
            (r'(%r([\W_]))((?:\\\2|(?!\2).)*)(\2[mixounse]*)',
             intp_regex_callback),
            # regular fancy strings with qsw
            (r'%[qsw]([\W_])((?:\\\1|(?!\1).)*)\1', String.Other),
            (r'(%[QWx]([\W_]))((?:\\\2|(?!\2).)*)(\2)',
             intp_string_callback),
            # special forms of fancy strings after operators or
            # in method calls with braces
            (r'(?<=[-+/*%=<>&!^|~,(])(\s*)(%([\t ])(?:(?:\\\3|(?!\3).)*)\3)',
             bygroups(Text, String.Other, None)),
            # and because of fixed width lookbehinds the whole thing a
            # second time for line startings...
            (r'^(\s*)(%([\t ])(?:(?:\\\3|(?!\3).)*)\3)',
             bygroups(Text, String.Other, None)),
            # all regular fancy strings without qsw
            (r'(%([^a-zA-Z0-9\s]))((?:\\\2|(?!\2).)*)(\2)',
             intp_string_callback),
        ]

        return states

    tokens = {
        'root': [
            (r'\A#!.+?$', Comment.Hashbang),
            (r'#.*?$', Comment.Single),
            # keywords
            (words((
                'begin', 'end', 'goto', 'jnz', 'jz',
                'io', 'wait', 'signal', 'alocar', 'liberar',
                'abrir', 'return', 'borrar', 'cerrar', 'buscar', 'escribir', 'leer'), suffix=r'\b'),
             Keyword),
            # start of function, class and module names
            (r'(function)(\s+)', bygroups(Keyword, Text), 'funcname'),
            (r'(variables)(\s+)', bygroups(Keyword, Name.Variable), 'funcname'),
            (r'function(?=[*%&^`~+-/\[<>=])', Keyword, 'funcname'),
            # special methods
            (r'(not|and|or)\b', Operator.Word),
            (words(('exit', 'quit'), suffix=r'\b'),
             Name.Builtin),
            (words((
                'Array', 'Float', 'Integer', 'String', '__id__', '__send__', 'abort',
                'ancestors', 'at_exit', 'autoload', 'binding', 'callcc', 'caller',
                'catch', 'class_eval', 'class_variables',
                'clone', 'const_defined?', 'const_get', 'const_missing', 'const_set',
                'constants', 'display', 'dup', 'eval', 'exec', 'extend', 'fail', 'fork',
                'format', 'freeze', 'getc', 'gets', 'global_variables',
                'hash', 'id', 'included_modules', 'inspect', 'instance_eval',
                'instance_method', 'instance_methods',
                'instance_variable_get', 'instance_variable_set', 'instance_variables',
                'lambda', 'load', 'local_variables', 'loop',
                'method', 'method_missing', 'methods', 'module_eval', 'name',
                'object_id', 'open', 'p', 'print', 'printf', 'private_class_method',
                'private_instance_methods',
                'private_methods', 'proc', 'protected_instance_methods',
                'protected_methods', 'public_class_method',
                'public_instance_methods', 'public_methods',
                'putc', 'puts', 'raise', 'rand', 'readline', 'readlines', 'require',
                'scan', 'select', 'self', 'send', 'set_trace_func', 'singleton_methods', 'sleep',
                'split', 'sprintf', 'srand', 'syscall', 'system', 'taint',
                'test', 'throw', 'to_a', 'to_s', 'trace_var', 'trap', 'untaint',
                'untrace_var', 'warn'), prefix=r'(?<!\.)', suffix=r'\b'),
             Keyword.Pseudo),
            (r'__(FILE|LINE)__\b', Name.Builtin.Pseudo),

            (r'__END__', Comment.Preproc, 'end-part'),
            # multiline regex (after keywords or assignments)
            (r'(?:^|(?<=[=<>~!:])|'
             r'(?<=(?:\s|;)when\s)|'
             r'(?<=(?:\s|;)or\s)|'
             r'(?<=(?:\s|;)and\s)|'
             r'(?<=\.index\s)|'
             r'(?<=\.scan\s)|'
             r'(?<=\.sub\s)|'
             r'(?<=\.sub!\s)|'
             r'(?<=\.gsub\s)|'
             r'(?<=\.gsub!\s)|'
             r'(?<=\.match\s)|'
             r'(?<=(?:\s|;)if\s)|'
             r'(?<=(?:\s|;)elsif\s)|'
             r'(?<=^when\s)|'
             r'(?<=^index\s)|'
             r'(?<=^scan\s)|'
             r'(?<=^sub\s)|'
             r'(?<=^gsub\s)|'
             r'(?<=^sub!\s)|'
             r'(?<=^gsub!\s)|'
             r'(?<=^match\s)|'
             r'(?<=^if\s)|'
             r'(?<=^elsif\s)'
             r')(\s*)(/)', bygroups(Text, String.Regex), 'multiline-regex'),
            # multiline regex (in method calls or subscripts)
            (r'(?<=\(|,|\[)/', String.Regex, 'multiline-regex'),
            # multiline regex (this time the funny no whitespace rule)
            (r'(\s+)(/)(?![\s=])', bygroups(Text, String.Regex),
             'multiline-regex'),
            # lex numbers and ignore following regular expressions which
            # are division operators in fact (grrrr. i hate that. any
            # better ideas?)
            # since pygments 0.7 we also eat a "?" operator after numbers
            # so that the char operator does not work. Chars are not allowed
            # there so that you can use the ternary operator.
            # stupid example:
            #   x>=0?n[x]:""
            (r'(0_?[0-7]+(?:_[0-7]+)*)(\s*)([/?])?',
             bygroups(Number.Oct, Text, Operator)),
            (r'(0x[0-9A-Fa-f]+(?:_[0-9A-Fa-f]+)*)(\s*)([/?])?',
             bygroups(Number.Hex, Text, Operator)),
            (r'(0b[01]+(?:_[01]+)*)(\s*)([/?])?',
             bygroups(Number.Bin, Text, Operator)),
            (r'([\d]+(?:_\d+)*)(\s*)([/?])?',
             bygroups(Number.Integer, Text, Operator)),
            # Names
            (r'@@[a-zA-Z_]\w*', Name.Variable.Class),
            (r'@[a-zA-Z_]\w*', Name.Variable.Instance),
            (r'\$\w+', Name.Label),
            (r'\$[!@&`\'+~=/\\,;.<>_*$?:"^-]', Name.Variable.Global),
            (r'\$-[0adFiIlpvw]', Name.Variable.Global),
            (r'::', Operator),
            include('strings'),
            # chars
            (r'\?(\\[MC]-)*'  # modifiers
             r'(\\([\\abefnrstv#"\']|x[a-fA-F0-9]{1,2}|[0-7]{1,3})|\S)'
             r'(?!\w)',
             String.Char),
            (r'[A-Z]\w+', Name.Constant),
            # this is needed because ruby attributes can look
            # like keywords (class) or like this: ` ?!?
            (words(ANSISOP_OPERATORS, prefix=r'(\.|::)'),
             bygroups(Operator, Name.Operator)),
            (r'(\.|::)([a-zA-Z_]\w*[!?]?|[*%&^`~+\-/\[<>=])',
             bygroups(Operator, Name)),
            (r'[a-zA-Z_]\w*[!?]?', Name),
            (r'(\[|\]|\*\*|<<?|>>?|>=|<=|<=>|=~|={3}|'
             r'!~|&&?|\|\||\.{1,3})', Operator),
            (r'[-+/*%=<>&!^|~]=?', Operator),
            (r'[(){};,/?:\\]', Punctuation),
            (r'\s+', Text)
        ],
        'funcname': [
            (r'\(', Punctuation, 'defexpr'),
            (r'(?:([a-zA-Z_]\w*)(\.))?'
             r'([a-zA-Z_]\w*[!?]?|\*\*?|[-+]@?|'
             r'[/%&|^`~]|\[\]=?|<<|>>|<=?>|>=?|===?)',
             bygroups(Name.Class, Operator, Name.Function), '#pop'),
            default('#pop')
        ],
        'classname': [
            (r'\(', Punctuation, 'defexpr'),
            (r'<<', Operator, '#pop'),
            (r'[A-Z_]\w*', Name.Class, '#pop'),
            default('#pop')
        ],
        'defexpr': [
            (r'(\))(\.|::)?', bygroups(Punctuation, Operator), '#pop'),
            (r'\(', Operator, '#push'),
            include('root')
        ],
        'in-intp': [
            (r'\{', String.Interpol, '#push'),
            (r'\}', String.Interpol, '#pop'),
            include('root'),
        ],
        'string-intp': [
            (r'#\{', String.Interpol, 'in-intp'),
            (r'#@@?[a-zA-Z_]\w*', String.Interpol),
            (r'#\$[a-zA-Z_]\w*', String.Interpol)
        ],
        'string-intp-escaped': [
            include('string-intp'),
            (r'\\([\\abefnrstv#"\']|x[a-fA-F0-9]{1,2}|[0-7]{1,3})',
             String.Escape)
        ],
        'interpolated-regex': [
            include('string-intp'),
            (r'[\\#]', String.Regex),
            (r'[^\\#]+', String.Regex),
        ],
        'interpolated-string': [
            include('string-intp'),
            (r'[\\#]', String.Other),
            (r'[^\\#]+', String.Other),
        ],
        'multiline-regex': [
            include('string-intp'),
            (r'\\\\', String.Regex),
            (r'\\/', String.Regex),
            (r'[\\#]', String.Regex),
            (r'[^\\/#]+', String.Regex),
            (r'/[mixounse]*', String.Regex, '#pop'),
        ],
        'end-part': [
            (r'.+', Comment.Preproc, '#pop')
        ]
    }
    tokens.update(gen_ansisopstrings_rules())

    def analyse_text(text):
        return shebang_matches(text, r'ansisop(1\.\d)?')


class AnsisopConsoleLexer(Lexer):
    name = 'Ansisop ars session'
    aliases = ['ars']
    mimetypes = ['text/x-ansisop-shellsession']

    _prompt_re = re.compile('ars\([a-zA-Z_]\w*\):\d{3}:\d+[>*"\'] '
                            '|>> |\?> ')

    def get_tokens_unprocessed(self, text):
        rblexer = AnsisopLexer(**self.options)

        curcode = ''
        insertions = []
        for match in line_re.finditer(text):
            line = match.group()
            m = self._prompt_re.match(line)
            if m is not None:
                end = m.end()
                insertions.append((len(curcode),
                                   [(0, Generic.Prompt, line[:end])]))
                curcode += line[end:]
            else:
                if curcode:
                    for item in do_insertions(
                            insertions, rblexer.get_tokens_unprocessed(curcode)):
                        yield item
                    curcode = ''
                    insertions = []
                yield match.start(), Generic.Output, line
        if curcode:
            for item in do_insertions(
                    insertions, rblexer.get_tokens_unprocessed(curcode)):
                yield item

import re


class DirectiveParser:
    NAME = 'directive'

    @staticmethod
    def parse_name(m):
        raise NotImplementedError()

    @staticmethod
    def parse_title(m):
        raise NotImplementedError()

    @staticmethod
    def parse_content(m):
        raise NotImplementedError()

    @staticmethod
    def parse_tokens(block, text, state):
        if state.depth() >= block.max_nested_level - 1:
            rules = list(block.rules)
            rules.remove(self.NAME)
        else:
            rules = block.rules
        child = state.child_state(text)
        block.parse(child, rules)
        return child.tokens

    @staticmethod
    def parse_options(m):
        text = m.group('options')
        if not text.strip():
            return []

        options = []
        for line in re.split(r'\n+', text):
            line = line.strip()[1:]
            if not line:
                continue
            i = line.find(':')
            k = line[:i]
            v = line[i + 1:].strip()
            options.append((k, v))
        return options


class BaseDirective:
    parser = DirectiveParser
    DIRECTIVE_PATTERN = None

    def __init__(self, plugins):
        self._methods = {}
        self.__plugins = plugins

    def register(self, name, fn):
        self._methods[name] = fn

    def parse_method(self, name, block, m, state):
        method = self._methods.get(name)
        if method:
            token = method(block, m, state)
        else:
            token = {
                'type': 'block_error',
                'raw': 'Unsupported directive: ' + name,
            }

        if isinstance(token, list):
            for tok in token:
                state.append_token(tok)
        else:
            state.append_token(token)
        return token

    def parse_directive(self, block, m, state):
        raise NotImplementedError()

    def __call__(self, md):
        md.block.register(
            self.parser.NAME,
            self.DIRECTIVE_PATTERN,
            self.parse_directive,
        )
        for plugin in self.__plugins:
            plugin.parser = self.parser
            plugin(self, md)


class DirectivePlugin:
    def __init__(self):
        self.parser = None

    def parse_options(self, m):
        return self.parser.parse_options(m)

    def parse_name(self, m):
        return self.parser.parse_name(m)

    def parse_title(self, m):
        return self.parser.parse_title(m)

    def parse_content(self, m):
        return self.parser.parse_content(m)

    def parse_tokens(self, block, text, state):
        return self.parser.parse_tokens(block, text, state)

    def parse(self, block, m, state):
        raise NotImplementedError()

    def __call__(self, md):
        raise NotImplementedError()

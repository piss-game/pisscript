"""
=== Pisscript ===

An esoteric programming language designed around the environment of
the household restroom.

"""

import re
import sys

### UTILITY ###

class PSError(Exception):
    def __init__(self, msg, ln):
        super().__init__(msg)
        self.msg = msg
        self.ln = ln

class PSSyntaxError(PSError):
    pass

class PSRuntimeError(PSError):
    pass

class Source:
    def __init__(self, text, source_file):
        self.text = text
        self.source_file = source_file

def load_source(path):
    with open(path, 'r') as fl:
        return Source(fl.read(), path)

def segfault():
    import ctypes;ctypes.string_at(0)

### PARSING ###

class TokenStream:
    def __init__(self, source):
        self.source = source
        self.char_index = 0
        self.ln = 1

    def has_reached_end(self):
        return self.char_index == len(self.source.text)
    
    def _next_token(self):
        if self.has_reached_end():
            return Token("eof", "", self.ln)

        next_string = self.get_curr_string()

        token_patterns = {
            r'[0-9]+': "number",
            r'tub': "verb",
            r'fill': "verb",
            r'pour': "verb",
            r'ejaculate': "verb",
            r'measure': "verb",
            r'stick': "verb",
            r' ': "no_token",
            r'\n': "endl",
            r'".+?"': "string",
            r'[a-zA-Z_][a-zA-Z_0-9]{0,}': "name",
        }

        for pattern, token_type in token_patterns.items():
            match_obj = re.match(pattern, next_string)

            if match_obj:
                match = match_obj[0]
                self._consume_string(match)

                # quick sanity check
                if token_type == "string" and "\n" in match:
                    raise PSSyntaxError("Unterminated string literal", self.ln)

                # remove quotes from string
                if token_type == "string":
                    match = match[1:-1]
                
                # end
                return Token(token_type, match, self.ln)

        raise PSSyntaxError(f"Unexpected token {repr(next_string[0])}", self.ln)

    def _consume_string(self, string):
        for i in range(len(string)):
            char = self._next_char()

            if char == "\n":
                self.ln += 1

    def next_token(self):
        token = self._next_token()

        while token.type == "no_token":
            token = self._next_token()

        return token

    def _next_char(self):
        char = self.source.text[self.char_index]
        self.char_index+=1
        return char

    def _peek_char(self):
        return self.source.text[self.char_index]
    
    def get_curr_string(self):
        return self.source.text[self.char_index:]

class Token:
    def __init__(self, type, content, line):
        self.type = type
        self.content = content
        self.line = line

    def __repr__(self):
        return f'<Token type={repr(self.type)} content={repr(self.content)}>'
    
    def is_eof(self):
        return self.type == "eof"

class Statement:
    def __init__(self, verb, args, line):
        self.verb = verb
        self.args = args
        self.line = line
    
    def get_arg(self, n):
        if n >= len(self.args):
            return None
        return self.args[n]

class Parser:
    def __init__(self, source):
        self.source = source
        self.stream = TokenStream(source)
        self.instructions = []
    
    def parse(self):
        while not self.stream.has_reached_end():
            self._parse_statement()
    
    def _parse_statement(self):
        verb = self.stream.next_token()
        line = self.stream.ln

        # statement is blank line
        if verb.type == "endl":
            return
        
        if verb.type != "verb":
            raise PSSyntaxError(f"Expected statement, found token {repr(verb.content)}", self.stream.ln)
        
        # get args (up until ENDL or EOF)

        args = []

        while True:
            token = self.stream.next_token()

            if token.type == "endl" or token.type == "eof":
                break

            args.append(token)
            
        self.instructions.append(Statement(verb.content, args, line))

### RUNTIME ###

class Tub:
    def __init__(self, name):
        self.type = "number"
        self.value = 0
    
    def set_val(self, value):
        if type(value) == str:
            self.type = "string"
        else:
            self.type = "number"
        
        self.value = value

        if self.type == "number":
            if self.value < 0:
                segfault()

class PisscriptRuntime:
    def __init__(self, source):
        self.source = source
        self.parser = Parser(source)
        self.tubs = {}
        self.instructions = []
        self.callstack = []
        self.program_counter = 0
        self.ln = 0
    
    def add_tub(self, name):
        if name in self.tubs:
            self.throw_runtime_err(f"Tub with name {repr(name)} already exists!")
        
        self.tubs[name] = Tub(name)

    def throw_runtime_err(self, msg):
        raise PSRuntimeError(msg, self.ln)
    
    def run(self):
        error_type = None
        error = None
        try:
            self._run()
        except PSRuntimeError as err:
            error_type = "Runtime Error"
            error = err
        except PSSyntaxError as err:
            error_type = "Syntax Error"
            error = err
        finally:
            if error_type:
                print(f"\033[91m{self.source.source_file}:{error.ln}")
                print(f"{error_type}: {error.msg}")
                print(" | "+self.source.text.split("\n")[error.ln-1].strip())
                print("   ^^^^")
                print("that's kinda mungus moment if u ask me ඞ\033[0m")
    
    def _assert_token_type(self, token, type):
        if token.type != type:
            self.throw_runtime_err(f"Expected token of type {repr(type)}, found token {repr(token.content)}")

    def resolve_tub(self, name):
        if not name in self.tubs:
            self.throw_runtime_err(f"No Tub exists with name {repr(name)}")
        return self.tubs[name]

    def _run(self):
        self.parser.parse()
        self.instructions = self.parser.instructions
        
        while self.program_counter < len(self.instructions):
            inst = self._load_curr_instruction()
            self.ln = inst.line

            if inst.verb == "tub":
                name_token = inst.get_arg(0)
                if name_token is None:
                    self.throw_runtime_err("Expected Tub name")
                
                self._assert_token_type(name_token, "name")

                self.add_tub(name_token.content)
            
            if inst.verb == "ejaculate":
                load = inst.get_arg(0)
                if load is None:
                    self.throw_runtime_err("Expected expression (need something to ejaculate!)")
                
                if load.type == "name":
                    print(self.resolve_tub(load.content).value)
                else:
                    print(load.content)

            self.program_counter+=1

    def _load_curr_instruction(self):
        return self.instructions[self.program_counter]

    def _jmp(self, to):
        self.program_counter = to

    def _return(self):
        pass


### TESTING ###

if __name__=="__main__":
    if len(sys.argv) < 2:
        print("Error: no input files specified")
        quit()

    input_file = sys.argv[1]
    src = load_source(input_file)
    runtime = PisscriptRuntime(src)

    runtime.run()






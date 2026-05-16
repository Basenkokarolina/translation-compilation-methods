import re
import sys

# ЛР1
def clean_code(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(f"ERROR: файл '{input_file}' не найден")
        return False

    if code.count("/*") != code.count("*/"):
        print("ERROR: незакрытый многострочный комментарий")
        return False

    code_no_comments = re.sub(r"/\*[\s\S]*?\*/", "", code)
    code_no_comments = re.sub(r"//.*", "", code_no_comments)

    code_no_strings = re.sub(r'"(?:[^"\\]|\\.)*"', "", code_no_comments)
    code_no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "", code_no_strings)

    invalid_chars = []

    for i, char in enumerate(code_no_strings):
        if not (32 <= ord(char) <= 126 or char in "\n\t"):
            invalid_chars.append((char, i))

    if invalid_chars:
        print("ERROR: обнаружены недопустимые символы")
        for char, pos in invalid_chars:
            print(f"- символ '{char}' в позиции {pos}")
        return False

    code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    code = re.sub(r"//.*", "", code)

    cleaned_lines = []

    for line in code.split("\n"):
        line = line.strip()

        if not line:
            continue

        parts = re.split(r'(".*?"|\'.*?\')', line)
        new_line = ""

        for part in parts:
            if part.startswith('"') or part.startswith("'"):
                new_line += part
            else:
                part = " ".join(part.split())
                part = re.sub(r"\s+;", ";", part)
                part = re.sub(r"\s+\)", ")", part)
                part = re.sub(r"\(\s+", "(", part)
                new_line += part

        cleaned_lines.append(new_line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_lines))

    return True


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ЛР2 
KEYWORDS = {
    "include", "using", "namespace",
    "int", "bool", "main",
    "if", "return"
}

BOOL_CONST = {"true", "false"}

OPERATORS = {"#", "::", "=", "<<", "<", ">", "."}

DELIMITERS = {"(", ")", "{", "}", ";", '"', "<", ">"}


def lexer(code):
    tokens = []
    errors = []

    i = 0
    n = len(code)

    while i < n:
        c = code[i]

        if c.isspace():
            i += 1
            continue

        if c == '"':
            j = i + 1

            while j < n and code[j] != '"':
                j += 1

            if j >= n:
                errors.append("ERROR: незакрытый строковый литерал")
                tokens.append(("CONSTANT_STRING", code[i + 1:]))
                i = n
                continue

            value = code[i:j + 1]
            tokens.append(("CONSTANT_STRING", value))
            i = j + 1
            continue

        if code[i:i + 2] in OPERATORS:
            tokens.append(("OPERATOR", code[i:i + 2]))
            i += 2
            continue

        if c in "#=<>;(){}.":
            if c in "#=<>" or c == ".":
                tokens.append(("OPERATOR", c))
            else:
                tokens.append(("DELIMITER", c))
            i += 1
            continue

        if c.isdigit():
            j = i
            dot_count = 0

            while j < n and (code[j].isdigit() or code[j] == "."):
                if code[j] == ".":
                    dot_count += 1
                j += 1

            number = code[i:j]

            if dot_count > 1:
                errors.append(f"ERROR: некорректное число -> {number}")
                tokens.append(("ERROR", number))
                i = j
                continue

            if j < n and (code[j].isalpha() or code[j] == "_"):
                k = j

                while k < n and (code[k].isalnum() or code[k] == "_"):
                    k += 1

                word = code[j:k]
                bad = code[i:k]

                if word in KEYWORDS:
                    errors.append(
                        f"ERROR: некорректная лексема "
                        f"(число + ключевое слово) -> {bad}"
                    )
                else:
                    errors.append(
                        f"ERROR: идентификатор не может начинаться с цифры -> {bad}"
                    )

                tokens.append(("ERROR", bad))
                i = k
                continue

            tokens.append(("CONSTANT_INT", number))
            i = j
            continue

        if c.isalpha() or c == "_":
            j = i

            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1

            word = code[i:j]

            if word in KEYWORDS:
                tokens.append(("KEYWORD", word))
            elif word in BOOL_CONST:
                tokens.append(("CONSTANT_BOOL", word))
            else:
                tokens.append(("IDENTIFIER", word))

            i = j
            continue

        errors.append(f"ERROR: недопустимый символ -> {c}")
        i += 1

    return tokens, errors


def print_lexeme_table(tokens):
    print("Результат лексического анализа")
    print("Лексема              | Тип")
    print("---------------------+----------------")

    for token_type, lexeme in tokens:
        print(f"{lexeme:<20} | {token_type}")

# ЛР3
class ASTNode:
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, node):
        self.children.append(node)

    def is_hidden_in_ast(self):
        hidden_prefixes = (
            "value_type:",
            "initialized:",
            "condition_type:",
            "stream_type:",
        )
        return self.name.startswith(hidden_prefixes)

    def print_tree(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        print(prefix + connector + self.name)

        prefix += "    " if is_last else "│   "

        visible_children = []

        for child in self.children:
            if not child.is_hidden_in_ast():
                visible_children.append(child)

        for i, child in enumerate(visible_children):
            child.print_tree(prefix, i == len(visible_children) - 1)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "EOF")

    def eat(self, expected_type=None, expected_value=None):
        token = self.current()
        token_type = token[0]
        token_value = token[1]

        if expected_type and token_type != expected_type:
            self.errors.append(
                f"ERROR: ожидался тип {expected_type}, "
                f"получен {token_type} ('{token_value}') "
                f"в позиции {self.pos}"
            )
        elif expected_value and token_value != expected_value:
            self.errors.append(
                f"ERROR: ожидалось '{expected_value}', "
                f"получено '{token_value}' в позиции {self.pos}"
            )

        self.pos += 1
        return token

    def parse_program(self):
        root = ASTNode("Program")

        root.add(self.parse_include())
        root.add(self.parse_using())
        root.add(self.parse_main())

        if self.current()[0] != "EOF":
            self.errors.append(
                f"ERROR: лишние токены после конца программы "
                f"в позиции {self.pos}"
            )

        return root

    def parse_include(self):
        node = ASTNode("IncludeDirective")

        self.eat("OPERATOR", "#")
        self.eat("KEYWORD", "include")
        self.eat("OPERATOR", "<")

        lib = self.eat("IDENTIFIER")
        node.add(ASTNode(f"library: {lib[1]}"))

        self.eat("OPERATOR", ">")

        return node

    def parse_using(self):
        node = ASTNode("UsingNamespace")

        self.eat("KEYWORD", "using")
        self.eat("KEYWORD", "namespace")

        name = self.eat("IDENTIFIER")
        node.add(ASTNode(f"name: {name[1]}"))

        self.eat("DELIMITER", ";")

        return node

    def parse_main(self):
        node = ASTNode("FunctionDecl")

        return_type = self.eat("KEYWORD", "int")
        func_name = self.eat("KEYWORD", "main")

        self.eat("DELIMITER", "(")
        self.eat("DELIMITER", ")")
        self.eat("DELIMITER", "{")

        body = self.parse_body()

        self.eat("DELIMITER", "}")

        node.add(ASTNode(f"return_type: {return_type[1]}"))
        node.add(ASTNode(f"name: {func_name[1]}"))
        node.add(body)

        return node

    def parse_body(self):
        body = ASTNode("Body")

        while self.current()[0] != "EOF" and self.current()[1] != "}":
            token_type, token_value = self.current()

            if token_type == "KEYWORD" and token_value == "bool":
                body.add(self.parse_var_decl())
            elif token_type == "KEYWORD" and token_value == "if":
                body.add(self.parse_if())
            elif token_type == "KEYWORD" and token_value == "return":
                body.add(self.parse_return())
            elif token_type == "IDENTIFIER" and token_value == "cout":
                body.add(self.parse_output())
            else:
                self.errors.append(
                    f"ERROR: неизвестная конструкция '{token_value}' "
                    f"в позиции {self.pos}"
                )
                self.pos += 1

        return body

    def parse_var_decl(self):
        node = ASTNode("VarDecl")

        var_type = self.eat("KEYWORD", "bool")
        identifier = self.eat("IDENTIFIER")

        initialized = False
        value = ("EMPTY", "-")

        if self.current()[1] == "=":
            self.eat("OPERATOR", "=")
            value = self.current()
            self.eat()
            initialized = True

        self.eat("DELIMITER", ";")

        node.add(ASTNode(f"type: {var_type[1]}"))
        node.add(ASTNode(f"name: {identifier[1]}"))
        node.add(ASTNode(f"value: {value[1]}"))
        node.add(ASTNode(f"value_type: {value[0]}"))
        node.add(ASTNode(f"initialized: {initialized}"))

        return node

    def parse_if(self):
        node = ASTNode("IfStmt")

        self.eat("KEYWORD", "if")
        self.eat("DELIMITER", "(")

        condition = self.current()
        self.eat()

        self.eat("DELIMITER", ")")
        self.eat("DELIMITER", "{")

        body = self.parse_body()

        self.eat("DELIMITER", "}")

        node.add(ASTNode(f"condition: {condition[1]}"))
        node.add(ASTNode(f"condition_type: {condition[0]}"))
        node.add(body)

        return node

    def parse_output(self):
        node = ASTNode("OutputStmt")

        self.eat("IDENTIFIER", "cout")
        self.eat("OPERATOR", "<<")

        first_value = self.current()
        self.eat()

        self.eat("OPERATOR", "<<")

        second_value = self.current()
        self.eat()

        self.eat("DELIMITER", ";")

        if first_value[0] == "CONSTANT_STRING":
            node.add(ASTNode(f"string: {first_value[1][1:-1]}"))
        else:
            node.add(ASTNode(f"value: {first_value[1]}"))
            node.add(ASTNode(f"value_type: {first_value[0]}"))

        node.add(ASTNode(f"stream: {second_value[1]}"))
        node.add(ASTNode(f"stream_type: {second_value[0]}"))

        return node

    def parse_return(self):
        node = ASTNode("ReturnStmt")

        self.eat("KEYWORD", "return")

        value = self.current()
        self.eat()

        self.eat("DELIMITER", ";")

        node.add(ASTNode(f"value: {value[1]}"))
        node.add(ASTNode(f"value_type: {value[0]}"))

        return node

#ЛР4
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.triads = []
        self.current_function_type = None

        self.builtin = {
            "std": "namespace",
            "iostream": "library",
            "cout": "ostream",
            "endl": "ostream"
        }

    def get_value(self, node, prefix):
        for child in node.children:
            if child.name.startswith(prefix):
                return child.name.split(": ", 1)[1]
        return None

    def add_symbol(self, name, var_type, declared=True, initialized=False):
        if name in self.symbol_table:
            self.errors.append(
                f"ERROR: повторное объявление переменной '{name}' "
                f"в одной области видимости"
            )
            return

        self.symbol_table[name] = {
            "type": var_type,
            "declared": declared,
            "initialized": initialized
        }

    def get_constant_type(self, token_type):
        if token_type == "CONSTANT_INT":
            return "int"
        if token_type == "CONSTANT_BOOL":
            return "bool"
        if token_type == "CONSTANT_STRING":
            return "string"
        if token_type == "IDENTIFIER":
            return "identifier"
        if token_type == "EMPTY":
            return "empty"
        return "unknown"

    def analyze(self, node):
        if node.name == "Program":
            for child in node.children:
                self.analyze(child)

        elif node.name == "IncludeDirective":
            library = self.get_value(node, "library:")

            if library in self.builtin:
                self.add_symbol(library, self.builtin[library], True, False)
            else:
                self.errors.append(
                    f"ERROR: неизвестная библиотека '{library}'"
                )

        elif node.name == "UsingNamespace":
            name = self.get_value(node, "name:")

            if name in self.builtin:
                self.add_symbol(name, self.builtin[name], True, False)
            else:
                self.errors.append(
                    f"ERROR: неизвестное пространство имён '{name}'"
                )

        elif node.name == "FunctionDecl":
            self.current_function_type = self.get_value(node, "return_type:")

            for child in node.children:
                self.analyze(child)

        elif node.name == "Body":
            for child in node.children:
                self.analyze(child)

        elif node.name == "VarDecl":
            self.analyze_var_decl(node)

        elif node.name == "IfStmt":
            self.analyze_if(node)

        elif node.name == "OutputStmt":
            self.analyze_output(node)

        elif node.name == "ReturnStmt":
            self.analyze_return(node)

    def analyze_var_decl(self, node):
        var_type = self.get_value(node, "type:")
        name = self.get_value(node, "name:")
        value = self.get_value(node, "value:")
        value_type_token = self.get_value(node, "value_type:")
        initialized = self.get_value(node, "initialized:") == "True"
        value_type = self.get_constant_type(value_type_token)

        if initialized:
            if value_type == "identifier":
                if value not in self.symbol_table:
                    self.errors.append(
                        f"ERROR: использование необъявленной переменной '{value}'"
                    )
                else:
                    value_type = self.symbol_table[value]["type"]

            if var_type != value_type:
                self.errors.append(
                    f"ERROR: несоответствие типов: переменной '{name}' "
                    f"типа {var_type} нельзя присвоить значение '{value}' "
                    f"типа {value_type}"
                )

        self.add_symbol(name, var_type, True, initialized)

        if initialized:
            self.triads.append(f"(:=, {name}, {value})")

    def analyze_if(self, node):
        condition = self.get_value(node, "condition:")
        condition_type_token = self.get_value(node, "condition_type:")
        condition_type = self.get_constant_type(condition_type_token)

        if condition_type == "identifier":
            if condition not in self.symbol_table:
                self.errors.append(
                    f"ERROR: использование необъявленной переменной '{condition}'"
                )
            else:
                condition_type = self.symbol_table[condition]["type"]

                if not self.symbol_table[condition]["initialized"]:
                    self.errors.append(
                        f"ERROR: переменная '{condition}' используется без инициализации"
                    )

        if condition_type != "bool":
            self.errors.append(
                f"ERROR: условие if должно иметь тип bool, "
                f"получен тип {condition_type}"
            )

        false_jump = len(self.triads) + 4
        self.triads.append(f"(ifFalse, {condition}, ^{false_jump})")

        for child in node.children:
            if child.name == "Body":
                self.analyze(child)

    def analyze_output(self, node):
        string_value = self.get_value(node, "string:")
        value = self.get_value(node, "value:")
        stream = self.get_value(node, "stream:")

        if "cout" not in self.symbol_table:
            self.add_symbol("cout", "ostream", True, True)

        if stream not in self.symbol_table:
            if stream in self.builtin:
                self.add_symbol(stream, self.builtin[stream], True, True)
            else:
                self.errors.append(
                    f"ERROR: использование необъявленного идентификатора '{stream}'"
                )

        if string_value is not None:
            self.triads.append(f"(output, \"{string_value}\", cout)")
        elif value is not None:
            if value not in self.symbol_table and not value.isdigit() and value not in BOOL_CONST:
                self.errors.append(
                    f"ERROR: использование необъявленной переменной '{value}'"
                )
            self.triads.append(f"(output, {value}, cout)")

        self.triads.append(f"(output, {stream}, cout)")

    def analyze_return(self, node):
        value = self.get_value(node, "value:")
        value_type_token = self.get_value(node, "value_type:")
        value_type = self.get_constant_type(value_type_token)

        if value_type == "identifier":
            if value not in self.symbol_table:
                self.errors.append(
                    f"ERROR: использование необъявленной переменной '{value}'"
                )
            else:
                value_type = self.symbol_table[value]["type"]

                if not self.symbol_table[value]["initialized"]:
                    self.errors.append(
                        f"ERROR: переменная '{value}' используется без инициализации"
                    )

        if self.current_function_type != value_type:
            self.errors.append(
                f"ERROR: несоответствие типов: функция main имеет тип "
                f"{self.current_function_type}, но возвращает значение "
                f"'{value}' типа {value_type}"
            )

        self.triads.append(f"(return, {value}, -)")

    def print_symbol_table(self):
        print("Name     | Type      | Declared | Initialized")
        print("---------+-----------+----------+-------------")

        for name, data in self.symbol_table.items():
            print(
                f"{name:<8} | "
                f"{data['type']:<9} | "
                f"{str(data['declared']).lower():<8} | "
                f"{str(data['initialized']).lower():<11}"
            )

    def print_triads(self):
        for i, triad in enumerate(self.triads, start=1):
            print(f"{i}) {triad}")


def run_compiler(input_file="test.cpp", cleaned_file="cleaned.cpp"):
    print("ЛР1 — предпроцессинг")

    if clean_code(input_file, cleaned_file):
        print("Препроцессинг завершён успешно.")
        print(f"Очищенный файл сохранён: {cleaned_file}")
    else:
        print("Препроцессинг завершён с ошибками.")
        return

    code = read_file(cleaned_file)

    print("\nЛР2 — лексический анализатор")

    tokens, lex_errors = lexer(code)
    print_lexeme_table(tokens)

    print("\nСписок токенов:")
    print("[")
    print(", ".join([f"({token_type}, {lexeme})" for token_type, lexeme in tokens]))
    print("]")

    print("\nЛексический анализ завершён.")

    if lex_errors:
        print("Обнаружены лексические ошибки:")
        for error in lex_errors:
            print("-", error)
        return
    else:
        print(f"Ошибок не найдено. Обнаружено {len(tokens)} токенов.")

    print("\nЛР3 — синтаксический анализатор")

    parser = Parser(tokens)
    ast = parser.parse_program()

    print("Program")
    for i, child in enumerate(ast.children):
        child.print_tree("", i == len(ast.children) - 1)

    print("\nСинтаксический анализ завершён.")

    if parser.errors:
        print("Обнаружены синтаксические ошибки:")
        for error in parser.errors:
            print("-", error)
        return
    else:
        print("Ошибок не найдено.")

    print("\nЛР4 — Семантический анализатор")

    semantic = SemanticAnalyzer()
    semantic.analyze(ast)

    print("Таблица символов:")
    semantic.print_symbol_table()

    print("\nСемантический анализ завершён.")

    if semantic.errors:
        print("Обнаружены семантические ошибки:")
        for error in semantic.errors:
            print("-", error)
    else:
        print("Ошибок не найдено.")

    print("\nТриады:")
    semantic.print_triads()


if __name__ == "__main__":
    input_path = "lab1/test.cpp"
    output_path = "cleaned.cpp"

    if len(sys.argv) >= 2:
        input_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]

    run_compiler(input_path, output_path)

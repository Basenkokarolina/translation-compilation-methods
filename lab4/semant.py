KEYWORDS = {
    "include", "using", "namespace",
    "int", "bool", "main",
    "if", "return"
}

IDENTIFIERS = {
    "std", "a", "cout", "endl", "iostream"
}

BOOL_CONST = {
    "true", "false"
}

OPERATORS = {
    "#", "::", "=", "<<", "<", ">", "."
}

DELIMITERS = {
    "(", ")", "{", "}", ";"
}


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

#Лексический анализатор
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
                errors.append(
                    f"ERROR: незакрытый строковый литерал (позиция {i})"
                )
                tokens.append(("ERROR", code[i:]))
                break

            value = code[i:j + 1]
            tokens.append(("CONSTANT_STRING", value))
            i = j + 1
            continue

        if code[i:i + 2] in OPERATORS:
            tokens.append(("OPERATOR", code[i:i + 2]))
            i += 2
            continue

        if c in "#=<>.":
            tokens.append(("OPERATOR", c))
            i += 1
            continue

        if c in "(){};":
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

            value = code[i:j]

            if dot_count > 1:
                errors.append(
                    f"ERROR: некорректное число -> {value} (позиция {i})"
                )
                tokens.append(("ERROR", value))
                i = j
                continue

            if j < n and (code[j].isalpha() or code[j] == "_"):
                k = j

                while k < n and (code[k].isalnum() or code[k] == "_"):
                    k += 1

                bad = code[i:k]

                errors.append(
                    f"ERROR: идентификатор не может начинаться с цифры -> "
                    f"{bad} (позиция {i})"
                )

                tokens.append(("ERROR", bad))
                i = k
                continue

            tokens.append(("CONSTANT_INT", value))
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
            elif word in IDENTIFIERS:
                tokens.append(("IDENTIFIER", word))
            else:
                errors.append(
                    f"ERROR: неизвестная лексема -> {word} (позиция {i})"
                )
                tokens.append(("ERROR", word))

            i = j
            continue

        errors.append(
            f"ERROR: недопустимый символ -> {c} (позиция {i})"
        )
        i += 1

    return tokens, errors

class ASTNode:

    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, node):
        self.children.append(node)

    def print_tree(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        print(prefix + connector + self.name)

        prefix += "    " if is_last else "│   "

        for i, child in enumerate(self.children):
            child.print_tree(prefix, i == len(self.children) - 1)


#Синтаксический анализатор
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
                f"получен {token_type} (позиция {self.pos})"
            )

        elif expected_value and token_value != expected_value:
            self.errors.append(
                f"ERROR: ожидалось '{expected_value}', "
                f"получено '{token_value}' (позиция {self.pos})"
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
                f"(позиция {self.pos})"
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

        self.eat("KEYWORD", "int")
        self.eat("KEYWORD", "main")
        self.eat("DELIMITER", "(")
        self.eat("DELIMITER", ")")
        self.eat("DELIMITER", "{")

        body = ASTNode("Body")

        body.add(self.parse_var_decl())
        body.add(self.parse_if())
        body.add(self.parse_return())

        self.eat("DELIMITER", "}")

        node.add(ASTNode("return_type: int"))
        node.add(ASTNode("name: main"))
        node.add(body)

        return node

    def parse_var_decl(self):
        node = ASTNode("VarDecl")

        var_type = self.eat("KEYWORD", "bool")
        identifier = self.eat("IDENTIFIER")

        self.eat("OPERATOR", "=")

        value = self.eat("CONSTANT_BOOL")

        self.eat("DELIMITER", ";")

        node.add(ASTNode(f"type: {var_type[1]}"))
        node.add(ASTNode(f"name: {identifier[1]}"))
        node.add(ASTNode(f"value: {value[1]}"))

        return node

    def parse_if(self):
        node = ASTNode("IfStmt")

        self.eat("KEYWORD", "if")
        self.eat("DELIMITER", "(")

        condition = self.eat("IDENTIFIER")

        self.eat("DELIMITER", ")")
        self.eat("DELIMITER", "{")

        body = ASTNode("Body")
        body.add(self.parse_output())

        self.eat("DELIMITER", "}")

        node.add(ASTNode(f"condition: {condition[1]}"))
        node.add(body)

        return node

    def parse_output(self):
        node = ASTNode("OutputStmt")

        self.eat("IDENTIFIER", "cout")
        self.eat("OPERATOR", "<<")

        string = self.eat("CONSTANT_STRING")

        self.eat("OPERATOR", "<<")

        endl = self.eat("IDENTIFIER", "endl")

        self.eat("DELIMITER", ";")

        node.add(ASTNode(f"string: {string[1][1:-1]}"))
        node.add(ASTNode(f"stream: {endl[1]}"))

        return node

    def parse_return(self):
        node = ASTNode("ReturnStmt")

        self.eat("KEYWORD", "return")

        value = self.eat("CONSTANT_INT")

        self.eat("DELIMITER", ";")

        node.add(ASTNode(f"value: {value[1]}"))

        return node


#Семантический анализатор
class SemanticAnalyzer:

    def __init__(self):
        self.symbol_table = {}
        self.errors = []
        self.triads = []

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
                f"ERROR: повторное объявление переменной '{name}'"
            )
            return

        self.symbol_table[name] = {
            "type": var_type,
            "declared": declared,
            "initialized": initialized
        }

    def analyze(self, node):
        if node.name == "Program":
            for child in node.children:
                self.analyze(child)

        elif node.name == "IncludeDirective":
            library = self.get_value(node, "library:")

            if library in self.builtin:
                self.add_symbol(
                    library,
                    self.builtin[library],
                    True,
                    False
                )

        elif node.name == "UsingNamespace":
            name = self.get_value(node, "name:")

            if name in self.builtin:
                self.add_symbol(
                    name,
                    self.builtin[name],
                    True,
                    False
                )

        elif node.name == "FunctionDecl":
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

        if var_type == "bool":
            if value not in ["true", "false"]:
                self.errors.append(
                    f"ERROR: несоответствие типов: переменной '{name}' "
                    f"типа bool нельзя присвоить значение '{value}'"
                )

        self.add_symbol(name, var_type, True, value is not None)

        self.triads.append(f"(:=, {name}, {value})")

    def analyze_if(self, node):
        condition = self.get_value(node, "condition:")

        if condition not in self.symbol_table:
            self.errors.append(
                f"ERROR: использование необъявленной переменной '{condition}'"
            )

        elif self.symbol_table[condition]["type"] != "bool":
            self.errors.append(
                f"ERROR: условие if должно иметь тип bool, "
                f"но переменная '{condition}' имеет тип "
                f"{self.symbol_table[condition]['type']}"
            )

        false_jump = len(self.triads) + 4

        self.triads.append(f"(ifFalse, {condition}, ^{false_jump})")

        for child in node.children:
            if child.name == "Body":
                self.analyze(child)

    def analyze_output(self, node):
        string_value = self.get_value(node, "string:")
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

        self.triads.append(f"(output, \"{string_value}\", cout)")
        self.triads.append(f"(output, {stream}, cout)")


    def analyze_return(self, node):
        value = self.get_value(node, "value:")

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

if __name__ == "__main__":

    path = "lab2/cleaned.cpp"

    code = read_file(path)

    tokens, lex_errors = lexer(code)

    parser = Parser(tokens)
    ast = parser.parse_program()


    semantic = SemanticAnalyzer()
    semantic.analyze(ast)

    print("\nТаблица символов:")
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
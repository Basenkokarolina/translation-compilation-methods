KEYWORDS = {
    "include", "using", "namespace",
    "int", "bool", "main",
    "if", "return"
}

IDENTIFIERS = {
    "std",
    "a",
    "cout",
    "endl",
    "iostream"
}

BOOL_CONST = {
    "true",
    "false"
}

OPERATORS = {
    "#",
    "::",
    "=",
    "<<",
    "<",
    ">",
    "."
}

DELIMITERS = {
    "(",
    ")",
    "{",
    "}",
    ";"
}
def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def lexer(code):

    tokens = []
    errors = []

    i = 0
    n = len(code)

    while i < n:

        c = code[i]

        #Пробелы
        if c.isspace():
            i += 1
            continue

        #Строковые константы
        if c == '"':

            j = i + 1

            while j < n and code[j] != '"':
                j += 1

            if j >= n:

                errors.append(
                    f"ERROR: незакрытый строковый литерал "
                    f"(позиция {i})"
                )

                tokens.append(("ERROR", code[i:]))

                break

            value = code[i:j + 1]

            tokens.append(("CONSTANT_STRING", value))

            i = j + 1

            continue

        #Двухсимвольные операторы
        if code[i:i + 2] in OPERATORS:

            tokens.append(("OPERATOR", code[i:i + 2]))

            i += 2

            continue

        #Односимвольные операторы
        if c in "#=<>.":

            tokens.append(("OPERATOR", c))

            i += 1

            continue

        #Разделители
        if c in "(){};":

            tokens.append(("DELIMITER", c))

            i += 1

            continue

        #Числа
        if c.isdigit():

            j = i
            dot_count = 0

            while j < n and (
                    code[j].isdigit() or code[j] == "."
            ):

                if code[j] == ".":
                    dot_count += 1

                j += 1

            value = code[i:j]

            #Ошибки
            if dot_count > 1:

                errors.append(
                    f"ERROR: некорректное число -> "
                    f"{value} (позиция {i})"
                )

                tokens.append(("ERROR", value))

                i = j

                continue


            if j < n and (
                    code[j].isalpha() or code[j] == "_"
            ):

                k = j

                while k < n and (
                        code[k].isalnum() or code[k] == "_"
                ):
                    k += 1

                word = code[j:k]

                bad = code[i:k]

                if word in KEYWORDS:

                    errors.append(
                        f"ERROR: некорректная лексема "
                        f"(число + ключевое слово) -> "
                        f"{bad} (позиция {i})"
                    )

                else:

                    errors.append(
                        f"ERROR: идентификатор не может "
                        f"начинаться с цифры -> "
                        f"{bad} (позиция {i})"
                    )

                tokens.append(("ERROR", bad))

                i = k

                continue

            tokens.append(("CONSTANT_INT", value))

            i = j

            continue

        #Слова

        if c.isalpha() or c == "_":

            j = i

            while j < n and (
                    code[j].isalnum() or code[j] == "_"
            ):
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
                    f"ERROR: неизвестная лексема -> "
                    f"{word} (позиция {i})"
                )

                tokens.append(("ERROR", word))

            i = j

            continue

        #Неизвестные символы

        errors.append(
            f"ERROR: недопустимый символ -> "
            f"{c} (позиция {i})"
        )

        i += 1

    return tokens, errors

#AST NODE
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

            child.print_tree(
                prefix,
                i == len(self.children) - 1
            )


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
                f"ERROR: ожидался тип "
                f"{expected_type}, "
                f"получен {token_type} "
                f"(позиция {self.pos})"
            )

        elif expected_value and token_value != expected_value:

            self.errors.append(
                f"ERROR: ожидалось "
                f"'{expected_value}', "
                f"получено '{token_value}' "
                f"(позиция {self.pos})"
            )

        self.pos += 1

        return token


    def parse_program(self):

        root = ASTNode("Program")

        root.add(self.parse_include())

        root.add(self.parse_using())

        root.add(self.parse_main())

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

        # тип переменной
        var_type = self.eat("KEYWORD", "bool")

        # имя переменной
        identifier = self.eat("IDENTIFIER")

        # =
        self.eat("OPERATOR", "=")

        # значение
        value = self.eat("CONSTANT_BOOL")

        # ;
        self.eat("DELIMITER", ";")

        # AST
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

if __name__ == "__main__":

    path = "lab2/cleaned.cpp"

    code = read_file(path)

    tokens, lex_errors = lexer(code)

    parser = Parser(tokens)

    ast = parser.parse_program()

    print("Program")

    for i, child in enumerate(ast.children):

        child.print_tree("", i == len(ast.children) - 1)

    print("\nСинтаксический анализ завершён.")

    if parser.errors:

        print("Обнаружены ошибки:")

        for error in parser.errors:
            print("-", error)

    else:

        print("Ошибок не найдено.")
from collections import defaultdict

KEYWORDS = {
    "include", "using", "namespace",
    "int", "bool", "main",
    "if", "return"
}

BOOL_CONST = {"true", "false"}

OPERATORS = {"#", "::", "=", "<<", "<", ">", "."}

DELIMITERS = {"(", ")", "{", "}", ";", '"', "<", ">"}

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

        if c.isspace():
            i += 1
            continue

        if c == '"':
            j = i + 1

            while j < n and code[j] != '"':
                j += 1

            if j >= n:
                errors.append("ERROR: незакрытый строковый литерал")
                tokens.append(("CONSTANT_STRING", code[i+1:]))
                i = n
                continue

            value = code[i:j+1]
            tokens.append(("CONSTANT_STRING", value))
            i = j + 1
            continue

        if code[i:i+2] in OPERATORS:
            tokens.append(("OPERATOR", code[i:i+2]))
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

            if j < n and code[j].isalpha():
                k = j
                while k < n and code[k].isalnum():
                    k += 1

                word = code[j:k]
                bad = code[i:k]

                if word in KEYWORDS:
                    errors.append(
                        f"ERROR: некорректная лексема (число + ключевое слово) -> {bad}"
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

def print_table(tokens):
    print("РЕЗУЛЬТАТ")
    print("Лексема     | Тип")
    print("------------+----------------------")

    for lex, ttype in tokens:
        print(f"{lex:<12} | {ttype}")


if __name__ == "__main__":
    path = "cleaned.cpp"

    code = read_file(path)

    tokens, errors = lexer(code)

    print_table(tokens)

    print("\n[")

    print(", ".join([f"({t}, {l})" for t, l in tokens]))

    print("]")

    print("\nЛексический анализ завершён.")

    if errors:
        print("Обнаружены ошибки:")
        for e in errors:
            print("-", e)
    else:
        print(f"Ошибок не найдено. Обнаружено {len(tokens)} токенов.")
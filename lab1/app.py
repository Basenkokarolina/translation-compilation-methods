import re

def clean_code(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        print("ошибка чтения файла")
        return

    #Проверка на незакрытый многострочный комментарий
    if code.count("/*") != code.count("*/"):
        print("незакрытый многострочный комментарий")
        return

    #Удаляем комментарии и строковые литералы для проверки символов
    code_no_comments = re.sub(r'/\*[\s\S]*?\*/', '', code)
    code_no_comments = re.sub(r'//.*', '', code_no_comments)

    code_no_strings = re.sub(r'"(?:[^"\\]|\\.)*"', '', code_no_comments)
    code_no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", '', code_no_strings)

    #Проверка недопустимых символов
    invalid_chars = []

    for i, char in enumerate(code_no_strings):
        if not (32 <= ord(char) <= 126 or char in '\n\t'):
            invalid_chars.append((char, i))

    if invalid_chars:
        print("обнаружены недопустимые символы.")
        return


    #Удаление комментариев окончательно
    code = re.sub(r'/\*[\s\S]*?\*/', '', code)
    code = re.sub(r'//.*', '', code)

    cleaned_lines = []

    for line in code.split('\n'):
        line = line.strip()

        if not line:
            continue

        #Разделяем строку на код и строковые литералы
        parts = re.split(r'(".*?"|\'.*?\')', line)
        new_line = ""

        for part in parts:
            if part.startswith('"') or part.startswith("'"):
                new_line += part
            else:
                #Удаляем лишние пробелы
                part = " ".join(part.split())

                #пробел перед ;
                part = re.sub(r'\s+;', ';', part)

                #пробел перед )
                part = re.sub(r'\s+\)', ')', part)

                #пробел после (
                part = re.sub(r'\(\s+', '(', part)

                new_line += part

        cleaned_lines.append(new_line)

    with open(output_file, 'w', encoding='utf-8') as f: #Запись результата
        f.write('\n'.join(cleaned_lines))

    print("очистка прошла успешна")


if __name__ == "__main__":
    clean_code("test.cpp", "cleaned.cpp")

import os
import sys
import argparse
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


def is_text_file(file_path):
    """
    Проверяет, является ли файл текстовым.
    Возвращает True, если файл можно открыть как текст.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, PermissionError, OSError, IOError):
        return False


def is_editor_available(editor_name):
    """Проверяет, доступен ли редактор в системе."""
    return shutil.which(editor_name) is not None


def open_markdown_file(file_path):
    """
    Пытается открыть markdown-файл в доступном редакторе.
    Приоритет: Kate -> vim.
    Если ни один редактор не доступен, просто завершает работу.
    """
    # Проверяем наличие Kate
    if is_editor_available('kate'):
        print(f"Открываю файл в Kate: {file_path}")
        try:
            # Запускаем Kate с указанием файла
            subprocess.run(['kate', str(file_path)], check=False)
            return True
        except Exception as e:
            print(f"Ошибка при запуске Kate: {e}")
            # Продолжаем попытку с vim

    # Проверяем наличие vim
    if is_editor_available('vim'):
        print(f"Открываю файл в vim: {file_path}")
        try:
            # Запускаем vim с указанием файла
            subprocess.run(['vim', str(file_path)], check=False)
            return True
        except Exception as e:
            print(f"Ошибка при запуске vim: {e}")

    # Если ни один редактор не доступен
    print("Редакторы Kate и vim не найдены в системе.")
    print(f"Файл сохранен по пути: {file_path}")
    return False


def get_markdown_templates():
    """
    Сканирует подкаталог 'promts' в текущей директории на наличие .md файлов.
    Возвращает список путей к шаблонам.
    """
    templates_dir = Path("promts")
    templates = []

    if templates_dir.exists() and templates_dir.is_dir():
        # Ищем все .md файлы в директории promts
        for template_file in templates_dir.glob("*.md"):
            if template_file.is_file():
                templates.append(template_file)

    return templates


def select_template(templates):
    """
    Отображает нумерованный список шаблонов и позволяет пользователю выбрать один.
    Возвращает путь к выбранному шаблону или None, если шаблон не выбран.
    """
    if not templates:
        return None

    print("\n" + "="*50)
    print("ДОСТУПНЫЕ ШАБЛОНЫ MARKDOWN:")
    print("="*50)

    for i, template in enumerate(templates, 1):
        print(f"{i:3}. {template.name}")

    print("\nВведите номер шаблона для использования")
    print("или нажмите Enter для сохранения без шаблона")

    try:
        choice = input("Ваш выбор: ").strip()
        if not choice:
            return None

        index = int(choice) - 1
        if 0 <= index < len(templates):
            return templates[index]
        else:
            print(f"Ошибка: номер {choice} вне диапазона 1-{len(templates)}")
            return None
    except ValueError:
        print(f"Ошибка: '{choice}' не является числом")
        return None


def apply_template(template_path, generated_content):
    """
    Применяет шаблон к сгенерированному содержимому.
    Заменяет плейсхолдер [{{
    }}] в шаблоне на сгенерированное содержимое.
    Исправлено: использование простой конкатенации для избежания лишних символов.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Ищем плейсхолдер для замены - [{{
        # }}] (с переносами строк как в предоставленном примере)
        placeholder = "[{{\n}}]"

        if placeholder in template_content:
            # Используем конкатенацию вместо f-строки с двойными фигурными скобками
            # Это избегает проблемы с экранированием и появлением лишних символов \
            replacement_content = "[{{\n" + generated_content + "\n}}]"
            result_content = template_content.replace(placeholder, replacement_content)
            print(f"Шаблон '{template_path.name}' успешно применен")
            return result_content
        else:
            # Также проверяем альтернативный вариант плейсхолдера
            alt_placeholder = "[{{\n\n}}]"
            if alt_placeholder in template_content:
                replacement_content = "[{{\n" + generated_content + "\n}}]"
                result_content = template_content.replace(alt_placeholder, replacement_content)
                print(f"Шаблон '{template_path.name}' успешно применен")
                return result_content

            # Если не нашли точный плейсхолдер, попробуем более гибкий поиск
            import re
            # Ищем любой вариант [{{...}}] с возможными пробелами и переносами строк
            pattern = r'\[\{\{[\s\n]*\}\}\]'
            match = re.search(pattern, template_content)
            if match:
                found_placeholder = match.group(0)
                replacement_content = "[{{\n" + generated_content + "\n}}]"
                result_content = template_content.replace(found_placeholder, replacement_content)
                print(f"Шаблон '{template_path.name}' успешно применен")
                return result_content

            print(f"Внимание: шаблон '{template_path.name}' не содержит ожидаемого плейсхолдера [{{\n}}]")
            print("Содержимое шаблона будет использовано как есть")
            return template_content
    except Exception as e:
        print(f"Ошибка при чтении шаблона {template_path}: {e}")
        return generated_content


class TreeNode:
    """Узел дерева файловой системы (файл или каталог)"""
    def __init__(self, name, path, node_type, parent=None):
        self.name = name
        self.path = path
        self.type = node_type
        self.parent = parent
        self.children = []
        self.extensions = []
        self.selected = False
        self.line_number = None

    def add_child(self, child):
        """Добавление дочернего узла"""
        self.children.append(child)

    def get_selection_state_char(self):
        """Получение символа состояния для отображения в дереве"""
        if self.type == 'file':
            return 'X' if self.selected else ' '
        else:
            return '.'

    def toggle(self):
        """Переключение состояния выбора для файла"""
        if self.type == 'file':
            self.selected = not self.selected

    def invert_selection(self, recursive=False):
        """ИНВЕРТИРОВАНИЕ отметок всех файлов в каталоге"""
        if self.type != 'directory':
            return

        def invert_node(node):
            if node.type == 'file':
                node.selected = not node.selected
            elif recursive and node.type == 'directory':
                for child in node.children:
                    invert_node(child)

        for child in self.children:
            if child.type == 'file':
                child.selected = not child.selected
            elif recursive:
                for grandchild in child.children:
                    invert_node(grandchild)

    def select_all(self, recursive=False):
        """ВЫДЕЛЕНИЕ ВСЕХ файлов в каталоге"""
        if self.type != 'directory':
            return

        def select_node(node):
            if node.type == 'file':
                node.selected = True
            elif recursive and node.type == 'directory':
                for child in node.children:
                    select_node(child)

        for child in self.children:
            if child.type == 'file':
                child.selected = True
            elif recursive:
                for grandchild in child.children:
                    select_node(grandchild)

    def deselect_all(self, recursive=False):
        """СНЯТИЕ ВЫДЕЛЕНИЯ со всех файлов в каталоге"""
        if self.type != 'directory':
            return

        def deselect_node(node):
            if node.type == 'file':
                node.selected = False
            elif recursive and node.type == 'directory':
                for child in node.children:
                    deselect_node(child)

        for child in self.children:
            if child.type == 'file':
                child.selected = False
            elif recursive:
                for grandchild in child.children:
                    deselect_node(grandchild)

    def toggle_extension(self, ext_index, recursive=False):
        """Выбор/снятие файлов с определенным расширением"""
        if self.type != 'directory':
            return

        # Находим расширение по индексу
        if ext_index < 1 or ext_index > len(self.extensions):
            return

        target_ext = self.extensions[ext_index-1][1]

        def process_node(node):
            if node.type == 'file':
                # Проверяем соответствие расширения
                if node.path.suffix.lower() == target_ext or (target_ext == '' and not node.path.suffix):
                    node.selected = not node.selected
            elif recursive and node.type == 'directory':
                # Рекурсивно обрабатываем детей
                for child in node.children:
                    process_node(child)

        # Обрабатываем файлы в текущем каталога и, если нужно, в подкаталогах
        for child in self.children:
            process_node(child)

    def get_selected_files(self):
        """Рекурсивный сбор всех выбранных файлов"""
        selected_files = []
        if self.type == 'file' and self.selected:
            selected_files.append(self.path)
        else:
            for child in self.children:
                selected_files.extend(child.get_selected_files())
        return selected_files

    def collect_extensions(self):
        """Сбор уникальных расширений в каталоге и подкаталогах (только текстовые файлы)"""
        extensions_set = set()
        if self.type == 'directory':
            for child in self.children:
                if child.type == 'file':
                    ext = child.path.suffix.lower()
                    extensions_set.add(ext if ext else '')
                else:
                    extensions_set.update(child.collect_extensions())
        return extensions_set

    def has_text_files(self):
        """Проверяет, содержит ли узел (каталог) текстовые файлы"""
        if self.type == 'file':
            return True
        else:
            for child in self.children:
                if child.has_text_files():
                    return True
            return False


class FileTree:
    """Класс для построения и управления деревом файловой системы"""
    def __init__(self, root_path, default_extensions):
        self.root_path = Path(root_path)
        self.default_extensions = default_extensions
        self.root = None
        self.line_to_node = {}
        self.build_tree()

    def build_tree(self):
        """Рекурсивное построение дерева начиная с корневой директории (только текстовые файлы)"""
        def build_node(current_path, parent=None):
            # Определяем имя узла
            if parent is None:
                node_name = self.root_path.name
            else:
                node_name = current_path.name

            node_type = 'directory' if current_path.is_dir() else 'file'
            node = TreeNode(node_name, current_path, node_type, parent)

            if node_type == 'directory' and 'build' not in str(current_path.relative_to(self.root_path)):
                try:
                    # Сначала собираем всех потенциальных детей
                    potential_children = []
                    for item in sorted(current_path.iterdir()):
                        if item.name.startswith('.'):
                            continue
                        if item.is_dir() and 'build' in str(item.relative_to(self.root_path)):
                            continue
                        potential_children.append(item)

                    # Рекурсивно строим детей
                    for item in potential_children:
                        child = build_node(item, node)
                        if child is not None:
                            # Для файлов проверяем, текстовые ли они
                            if child.type == 'file':
                                if is_text_file(child.path):
                                    node.add_child(child)
                                else:
                                    continue
                            else:
                                if child.has_text_files():
                                    node.add_child(child)
                                else:
                                    continue
                except PermissionError:
                    pass

            # Устанавливаем состояние по умолчанию для текстовых файлов в корневом каталоге
            if parent is None and node.type == 'directory':
                for child in node.children:
                    if child.type == 'file':
                        ext = child.path.suffix.lower()
                        if ext in self.default_extensions or (ext == '' and '' in self.default_extensions):
                            child.selected = True

            # Собираем расширения для каталогов (только если есть дети)
            if node.type == 'directory' and node.children:
                extensions = sorted(list(node.collect_extensions()))
                if extensions:
                    node.extensions = [(i+1, ext) for i, ext in enumerate(extensions)]

            # Возвращаем узел только если он файл или каталог с текстовыми файлами
            if node.type == 'file':
                return node
            elif node.type == 'directory':
                if parent is None or node.children:
                    return node
                else:
                    return None
            else:
                return node

        self.root = build_node(self.root_path)
        if self.root is None:
            print("В указанной директории нет текстовых файлов.")
            sys.exit(0)

    def print_tree(self):
        """Вывод дерева с нумерацией строк и выравниванием расширений по табуляции"""
        self.line_to_node = {}
        line_counter = [1]

        # Сначала собираем все строки для определения максимальной длины
        tree_lines = []

        def collect_lines(node, prefix="", is_last=True, depth=0):
            if depth == 0:
                tree_symbol = "└── "
                next_prefix = "    "
            else:
                tree_symbol = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")

            # Формируем базовую строку дерева (без расширений)
            state_char = node.get_selection_state_char()
            base_line = f"{line_counter[0]:3}  [{state_char}]   {prefix}{tree_symbol}{node.name}"

            # Сохраняем отображение номера строки на узел
            node.line_number = line_counter[0]
            self.line_to_node[line_counter[0]] = node

            # Сохраняем информацию о строке
            tree_lines.append({
                'base_line': base_line,
                'node': node,
                'line_number': line_counter[0]
            })

            line_counter[0] += 1

            # Рекурсивно обрабатываем детей для каталогов
            if node.type == 'directory':
                child_count = len(node.children)
                for i, child in enumerate(node.children):
                    collect_lines(child, next_prefix, i == child_count-1, depth+1)

        collect_lines(self.root)

        # Определяем максимальную длину базовой строки
        max_base_length = max(len(line['base_line']) for line in tree_lines)

        # Выводим дерево с выравниванием
        print("\n--- Интерактивный выбор расширений файлов ---\n")

        for line_info in tree_lines:
            base_line = line_info['base_line']
            node = line_info['node']

            if node.type == 'directory' and node.extensions:
                # Для каталога добавляем список расширений с выравниванием
                ext_list = ", ".join([f"{num}:{ext}" for num, ext in node.extensions])
                # Вычисляем необходимое количество пробелов для выравнивания
                spaces_needed = max_base_length - len(base_line) + 4
                # Выводим строку с выравниванием
                print(f"{base_line}{' ' * spaces_needed}[{ext_list}]")
            else:
                print(base_line)

        print()

    def process_user_input(self, user_input):
        """Обработка ввода пользователя согласно новой спецификации"""
        commands = user_input.strip().split()

        for cmd in commands:
            # 1. Сначала проверяем команды с префиксом + или -
            if cmd.startswith('+') or cmd.startswith('-'):
                prefix = cmd[0]
                cmd_body = cmd[1:]
                recursive = False

                # Проверяем наличие суффикса *
                if cmd_body.endswith('*'):
                    recursive = True
                    cmd_body = cmd_body[:-1]

                try:
                    line_num = int(cmd_body)
                    if line_num in self.line_to_node:
                        node = self.line_to_node[line_num]
                        if node.type == 'directory':
                            if prefix == '+':
                                node.select_all(recursive)
                            else:  # prefix == '-'
                                node.deselect_all(recursive)
                            continue
                except ValueError:
                    print(f"Неверный формат команды: {cmd}")
                    continue

            # 2. Затем проверяем команды с расширением (формат N-M или N-M*)
            if '-' in cmd:
                parts = cmd.split('-')
                if len(parts) == 2:
                    line_str, ext_str = parts
                    recursive = False

                    # Проверяем наличие суффикса * в части с расширением
                    if ext_str.endswith('*'):
                        recursive = True
                        ext_str = ext_str[:-1]

                    try:
                        line_num = int(line_str)
                        ext_num = int(ext_str)

                        if line_num in self.line_to_node:
                            node = self.line_to_node[line_num]
                            if node.type == 'directory':
                                node.toggle_extension(ext_num, recursive)
                                continue
                    except ValueError:
                        print(f"Неверный формат команды: {cmd}")
                        continue

            # 3. Затем проверяем команды со звездочкой (инвертирование с рекурсией)
            if cmd.endswith('*'):
                cmd_body = cmd[:-1]
                recursive = True

                try:
                    line_num = int(cmd_body)
                    if line_num in self.line_to_node:
                        node = self.line_to_node[line_num]
                        if node.type == 'directory':
                            node.invert_selection(recursive)
                            continue
                        else:
                            node.toggle()
                            continue
                except ValueError:
                    print(f"Неверный формат команды: {cmd}")
                    continue

            # 4. Простая команда (просто номер)
            try:
                line_num = int(cmd)
                if line_num in self.line_to_node:
                    node = self.line_to_node[line_num]
                    if node.type == 'directory':
                        node.invert_selection(recursive=False)
                    else:
                        node.toggle()
            except ValueError:
                print(f"Неверный номер строки: {cmd}")


def get_all_text_extensions(directory_path):
    """Собирает все уникальные расширения файлов, которые можно открыть как текст."""
    extensions_set = set()
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Ошибка: Каталог '{directory_path}' не существует.")
        return extensions_set

    for file_path in directory.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            if 'build' in str(file_path.relative_to(directory).parts):
                continue

            if is_text_file(file_path):
                ext = file_path.suffix.lower()
                if ext:
                    extensions_set.add(ext)
                else:
                    extensions_set.add('')

    return extensions_set


def should_process_file(file_path, allowed_extensions):
    """Проверяет, нужно ли обрабатывать файл на основе выбранных расширений."""
    if 'build' in str(file_path).split(os.sep):
        return False

    if file_path.suffix.lower() in allowed_extensions:
        return True

    if not file_path.suffix and '' in allowed_extensions:
        return True

    return False


def get_file_type(extension):
    """Определяет тип файла для форматирования в markdown."""
    type_mapping = {
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.c++': 'cpp',
        '.cc': 'cpp',
        '.mm': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hh': 'c',
        '.hpp': 'cpp',
        '.qml': 'js',
        '.txt': 'text',
        '.diff': 'diff',
        '.md': 'markdown',
        '.py': 'python',
        '.sh': 'bash',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.toml': 'toml',
        '.sql': 'sql',
        '.cmake': 'cmake',
        '': 'text',
    }
    if extension == 'CMAKELISTS.TXT':
        return 'cmake'
    return type_mapping.get(extension.lower(), 'text')


def generate_output_filename(base_directory_path, num_parent_dirs):
    """Генерирует имя файла в формате parent1-parent2-...-basename_timestamp.md"""
    path_parts = list(Path(base_directory_path).parts)
    basename_part = path_parts[-1]

    start_idx = max(0, len(path_parts) - 1 - num_parent_dirs)
    parent_parts = path_parts[start_idx : len(path_parts) - 1]

    prefix_parts = parent_parts + [basename_part]
    safe_prefix = "-".join(prefix_parts)
    safe_prefix_cleaned = "".join(c for c in safe_prefix if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{safe_prefix_cleaned}_{timestamp}.md"


def generate_markdown_content(files):
    """
    Генерирует содержимое Markdown из списка файлов.
    Возвращает строку с отформатированным содержимым.
    """
    content_lines = []

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as source_file:
                file_content = source_file.read()

            if file_path.name.upper() == 'CMAKELISTS.TXT':
                file_type = 'cmake'
            else:
                file_type = get_file_type(file_path.suffix)

            content_lines.append(f"# {file_path}")
            content_lines.append(f"```{file_type}")
            content_lines.append(file_content)
            if not file_content.endswith('\n'):
                content_lines.append('')
            content_lines.append("```")
            content_lines.append("")  # Пустая строка между файлами

            print(f"Обработан: {file_path}")

        except UnicodeDecodeError:
            print(f"Пропущен: {file_path} (проблемы с кодировкой)")
        except Exception as e:
            print(f"Ошибка при обработке {file_path}: {e}")

    return "\n".join(content_lines)


def write_to_markdown(files, base_directory_path, num_parent_dirs):
    """Записывает содержимое файлов в markdown файл с возможностью использования шаблона."""
    # Шаг 1: Генерируем содержимое из выбранных файлов
    print("\nШаг 2: Генерация содержимого из выбранных файлов...")
    generated_content = generate_markdown_content(files)

    # Шаг 2: Проверяем наличие шаблонов
    print("\nШаг 3: Проверка доступных шаблонов...")
    templates = get_markdown_templates()

    final_content = generated_content
    template_used = None

    if templates:
        # Предлагаем пользователю выбрать шаблон
        selected_template = select_template(templates)

        if selected_template:
            # Применяем выбранный шаблон
            final_content = apply_template(selected_template, generated_content)
            template_used = selected_template.name
    else:
        print("Каталог 'promts' не найден или не содержит .md файлов-шаблонов")

    # Шаг 3: Сохраняем результат в файл
    output_file = generate_output_filename(base_directory_path, num_parent_dirs)

    with open(output_file, 'w', encoding='utf-8') as md_file:
        md_file.write(final_content)

    # Информируем пользователя о результате
    print(f"\n{'='*60}")
    print("РЕЗУЛЬТАТ СОХРАНЕНИЯ:")
    print(f"{'='*60}")
    print(f"Файл: {output_file}")
    print(f"Количество обработанных файлов: {len(files)}")
    if template_used:
        print(f"Использован шаблон: {template_used}")
    else:
        print("Использован шаблон: нет (прямое сохранение)")
    print(f"{'='*60}")

    # Открываем файл в редакторе
    open_markdown_file(Path(output_file).resolve())


def main():
    parser = argparse.ArgumentParser(description='Сканирует исходные файлы и сохраняет их в markdown файл с интерактивным выбором расширений.')
    parser.add_argument('directory', help='Путь к каталогу для сканирования')
    parser.add_argument('num_parents', nargs='?', type=int, default=1,
                       help='Количество родительских каталогов для включения в имя файла (по умолчанию: 1)')
    args = parser.parse_args()

    directory_path = args.directory
    num_parent_dirs = args.num_parents

    if num_parent_dirs < 0:
        print("Количество родительских каталогов не может быть отрицательным.")
        sys.exit(1)

    default_extensions = {'.cpp', '.cxx', '.c++', '.cc', '.mm', '.c', '.h',
                         '.hh', '.hpp', '.qml', '.txt'}

    file_tree = FileTree(directory_path, default_extensions)

    file_tree.print_tree()

    print("Инструкции по выбору:")
    print("- Введите номер строки файла: отметить/снять файл")
    print("- Введите номер строки директории: инвертировать отметки всех файлов в директории")
    print("- Введите номер строки директории со звездочкой (например, '9*'): инвертировать отметки рекурсивно")
    print("- Введите '+номер' (например, '+9'): выделить все файлы в директории")
    print("- Введите '-номер' (например, '-9'): снять выделение со всех файлов в директории")
    print("- Введите '+номер*' (например, '+9*'): выделить все файлы рекурсивно")
    print("- Введите '-номер*' (например, '-9*'): снять выделение рекурсивно")
    print("- Введите 'номер-расширение' (например, '1-1'): инвертировать файлы с указанным расширением")
    print("- Введите 'номер-расширение*' (например, '1-1*'): инвертировать файлы с указанным расширением рекурсивно")
    print("- Можно указать несколько команд через пробел")
    print("- Нажмите Enter без ввода для перехода ко второму этапу\n")

    while True:
        try:
            user_input = input("Введите команды выбора > ").strip()

            if not user_input:
                break

            file_tree.process_user_input(user_input)

            print("\nОбновленное дерево:")
            file_tree.print_tree()

        except KeyboardInterrupt:
            print("\n\nПроцесс прерван пользователем.")
            sys.exit(0)
        except EOFError:
            print("\n\nВвод завершен.")
            break

    print("\nШаг 2: Сбор выбранных файлов...")
    selected_files = file_tree.root.get_selected_files()

    if not selected_files:
        print("Не выбрано ни одного файла. Выход.")
        sys.exit(0)

    print(f"Найдено файлов для обработки: {len(selected_files)}")

    write_to_markdown(selected_files, directory_path, num_parent_dirs)


if __name__ == "__main__":
    main()

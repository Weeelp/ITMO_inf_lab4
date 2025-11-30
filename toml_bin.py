# ---------------------------------------------------------
#   ПАРСИНГ ОДИНОЧНОГО TOML-ЗНАЧЕНИЯ
# ---------------------------------------------------------
def parse_toml_value(raw: str, quoted: bool):
    raw = raw.strip()
    if quoted:
        if raw == "":
            raise ValueError("TOML ERROR: пустая строка в кавычках запрещена")
        return raw

    if raw.startswith('[') and raw.endswith(']'):
        inner = raw[1:-1].strip()
        if not inner:
            raise ValueError("TOML ERROR: пустой массив запрещен")
        items = []
        buf = ""
        in_quotes = False
        for ch in inner:
            if ch in "\"'":
                in_quotes = not in_quotes
                buf += ch
            elif ch == "," and not in_quotes:
                items.append(parse_toml_value(buf.strip(), buf.strip().startswith('"') or buf.strip().startswith("'")))
                buf = ""
            else:
                buf += ch
        if buf:
            items.append(parse_toml_value(buf.strip(), buf.strip().startswith('"') or buf.strip().startswith("'")))

        for item in items:
            if isinstance(item, dict):
                raise ValueError("TOML ERROR: массив не может содержать словарь")
        return items

    if raw == "true":
        return True
    if raw == "false":
        return False

    if raw.isdigit() or (raw.startswith('-') and raw[1:].isdigit()):
        num = raw.lstrip('-')
        if len(num) > 1 and num.startswith('0'):
            raise ValueError(f"TOML ERROR: ведущие нули не разрешены → {raw}")
        return int(raw)

    if raw.count('.') == 1:
        left, right = raw.split('.', 1)
        left_digits = left.isdigit() or (left.startswith('-') and left[1:].isdigit())
        right_digits = right.isdigit()
        if left_digits and right_digits:
            left_abs = left.lstrip('-')
            if len(left_abs) > 1 and left_abs.startswith('0'):
                raise ValueError(f"TOML ERROR: ведущие нули не разрешены → {raw}")
            return float(raw)

    if raw == "":
        raise ValueError("TOML ERROR: пустое значение без кавычек запрещено")

    if any(ch.isdigit() for ch in raw) or raw in ("true", "false"):
        if not raw.isdigit() and \
           not (raw.startswith('-') and raw[1:].isdigit()) and \
           not (raw.count('.') == 1 and
                all(part.isdigit() or (part.startswith('-') and part[1:].isdigit())
                    for part in raw.split('.', 1))) and \
           not (raw in ("true", "false")):
            raise ValueError(f"TOML ERROR: некорректное значение → {raw}")

    return raw

# ---------------------------------------------------------
#   ПАРСИНГ TOML-БЛОКА В PYTHON СЛОВАРЬ
# ---------------------------------------------------------
def parse_toml_to_dict(filename: str):
    def has_cyrillic(s: str):
        for ch in s:
            o = ord(ch)
            if 0x0400 <= o <= 0x04FF or 0x0500 <= o <= 0x052F:
                return True
        return False

    result = {}
    current = None

    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1].strip()
            parts = []
            buf = ""
            in_quotes = False
            for ch in inner:
                if ch in "\"'":
                    in_quotes = not in_quotes
                elif ch == "." and not in_quotes:
                    parts.append(buf.strip())
                    buf = ""
                    continue
                buf += ch
            parts.append(buf.strip())

            cleaned = []
            for p in parts:
                if p == "":
                    raise ValueError("TOML ERROR: пустое имя таблицы запрещено")
                quoted = (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'"))
                name = p[1:-1] if quoted else p
                if has_cyrillic(name) and not quoted:
                    raise ValueError(f"Русское имя таблицы '{name}' должно быть в кавычках")
                cleaned.append(name)

            cur = result
            for name in cleaned:
                cur = cur.setdefault(name, {})
            current = cur
            continue

        if "=" in line:
            left, right = (part.strip() for part in line.split("=", 1))
            if left == "":
                raise ValueError("TOML ERROR: пустой ключ запрещен")
            quoted_key = (left.startswith('"') and left.endswith('"')) or (left.startswith("'") and left.endswith("'"))
            key = left[1:-1] if quoted_key else left
            if has_cyrillic(key) and not quoted_key:
                raise ValueError(f"Ключ '{key}' содержит русские буквы — он должен быть в кавычках")


            quoted_val = (right.startswith('"') and right.endswith('"')) or (right.startswith("'") and right.endswith("'"))
            val = right[1:-1] if quoted_val else right

            if current is None:
                current = result.setdefault("_root", {})

            current[key] = parse_toml_value(val, quoted_val)

    return result


# ---------------------------------------------------------
#   СЕРИАЛИЗАЦИЯ PYTHON СЛОВАРЯ В БИНАРНЫЙ ФАЙЛ
# ---------------------------------------------------------
def serialize_to_bin(d: dict, filename: str):

    def write_string(f, s: str):
        b = s.encode("utf-8")
        f.write(len(b).to_bytes(4, "big"))
        f.write(b)

    # Типы:
    # 01 — словарь
    # 02 — строка
    # 04 — int
    # 05 — float
    # 06 — bool
    # 07 - list


    def write_value(f, value):
        if isinstance(value, dict):
            write_dict(f, value)
        elif isinstance(value, str):
            f.write(b'\x02')
            write_string(f, value)
        elif isinstance(value, list):
            f.write(b'\x07')
            f.write(len(value).to_bytes(4, 'big'))
            for item in value:
                if isinstance(item, str) and item[0] == "[":
                    raise ValueError("TOML ERROR: список не может содержать список")
                write_value(f, item)
        elif isinstance(value, bool):
            f.write(b'\x06')
            write_string(f, "1" if value else "0")
        elif isinstance(value, int):
            f.write(b'\x04')
            write_string(f, str(value))
        elif isinstance(value, float):
            f.write(b'\x05')
            write_string(f, repr(value))
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    def write_dict(f, d):
        f.write(b'\x01')
        for key, value in d.items():
            write_string(f, key)
            write_value(f, value)
        f.write(b'\x03')

    with open(filename, 'wb') as f:
        write_dict(f, d)

# ---------------------------------------------------------
#   ДЕСЕРИАЛИЗАЦИЯ БИНАРНОГО ФАЙЛА В PYTHON СЛОВАРЬ
# ---------------------------------------------------------
def deserialize_from_bin(filename: str):

    def read_string(f):
        length = int.from_bytes(f.read(4), "big")
        return f.read(length).decode("utf-8")

    def read_array(f):
        length = int.from_bytes(f.read(4), 'big')
        result = []
        for _ in range(length):
            item_marker = f.read(1)
            f.seek(-1, 1)
            if item_marker == b'\x01':
                result.append(read_dict(f))
            elif item_marker == b'\x02':
                f.read(1)
                result.append(read_string(f))
            elif item_marker == b'\x04':
                f.read(1)
                result.append(int(read_string(f)))
            elif item_marker == b'\x05':
                f.read(1)
                result.append(float(read_string(f)))
            elif item_marker == b'\x06':
                f.read(1)
                result.append(read_string(f) == "1")
            elif item_marker == b'\x07':
                f.read(1)
                result.append(read_array(f))
        return result

    def read_dict(f):
        if f.read(1) != b'\x01':
            raise ValueError("Dict expected")
        result = {}
        while True:
            pos = f.tell()
            next_byte = f.read(1)
            if next_byte == b'\x03' or not next_byte:
                break
            f.seek(pos)
            key = read_string(f)
            type_marker = f.read(1)
            if type_marker == b'\x01':
                f.seek(-1, 1)
                value = read_dict(f)
            elif type_marker == b'\x02':
                value = read_string(f)
            elif type_marker == b'\x04':
                value = int(read_string(f))
            elif type_marker == b'\x05':
                value = float(read_string(f))
            elif type_marker == b'\x06':
                value = read_string(f) == "1"
            elif type_marker == b'\x07':
                value = read_array(f)
            else:
                raise ValueError(f"Unknown type marker {type_marker}")
            result[key] = value
        return result

    with open(filename, "rb") as f:
        return read_dict(f)

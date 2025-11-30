def deserialize_to_json(data, filename):
    def write_value(f, value, indent):
        if isinstance(value, dict):
            write_dict(f, value, indent)
        elif isinstance(value, list):
            write_list(f, value, indent)
        elif isinstance(value, str):
            val_str = value.replace('\\', '\\\\').replace('"', '\\"')
            f.write(f'"{val_str}"')
        elif isinstance(value, bool):
            f.write("true" if value else "false")
        elif isinstance(value, int) or isinstance(value, float):
            f.write(str(value))
        else:
            raise TypeError(f"Unsupported type: {type(value)}")

    def write_list(f, lst, indent):
        f.write("[\n")
        for i, item in enumerate(lst):
            f.write('  ' * (indent + 1))
            write_value(f, item, indent + 1)
            if i < len(lst) - 1:
                f.write(',')
            f.write('\n')
        f.write('  ' * indent + "]")

    def write_dict(f, d, indent=0):
        f.write('{\n')
        n = len(d)
        for i, (key, value) in enumerate(d.items()):
            if not key:
                f.truncate(0)
                raise ValueError("JSON ERROR: пустое значение запрещено")
            f.write('  ' * (indent + 1) + f'"{key}": ')
            write_value(f, value, indent + 1)
            if i < n - 1:
                f.write(',')
            f.write('\n')
        f.write('  ' * indent + '}')

    with open(filename, 'w', encoding='utf-8') as f:
        write_dict(f, data)
        f.write('\n')

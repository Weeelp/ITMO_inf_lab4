def deserialize_to_xml(data: dict, filename: callable, root_tag="root"):
    
    def escape_xml(s: str):
        s = str(s)
        s = s.replace("&", "&amp;")
        s = s.replace("<", "&lt;")
        s = s.replace(">", "&gt;")
        s = s.replace('"', "&quot;")
        s = s.replace("'", "&apos;")
        return s

    def write_dict(f, d, indent=0):
        for key, value in d.items():
            if not key :
                f.truncate(0)
                raise ValueError("XML ERROR: пустое значение запрещено")
            f.write('  ' * indent + f'<{key}>')
            if isinstance(value, dict):
                f.write('\n')
                write_dict(f, value, indent + 1)
                f.write('  ' * indent + f'</{key}>\n')
            else:
                f.write(f'{escape_xml(value)}</{key}>\n')

    f = open(filename, 'w', encoding='utf-8')
    try:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(f'<{root_tag}>\n')
        write_dict(f, data, 1)
        f.write(f'</{root_tag}>\n')
    finally:
        f.close()
     
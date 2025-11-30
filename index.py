from toml_bin import parse_toml_to_dict, serialize_to_bin, deserialize_from_bin
from bin_json import deserialize_to_json
from bin_xml import deserialize_to_xml
import time
start = time.time() 

try:
    import time
    start = time.time()

    d = parse_toml_to_dict("data/timetable.toml")
    serialize_to_bin(d, "data/timetable.bin")
    pydict = deserialize_from_bin("data/timetable.bin")

    # print(pydict, "<----------")

    deserialize_to_json(pydict, "data/timetalbe.json")

    print('Время работы: ', (time.time() - start) * 100)

    deserialize_to_xml( pydict, 'data/timetable.xml')

    print("Время работы + xml:", (time.time()-start)*1000, "мс")
except Exception as e:
    print(f"Ошибка из index.py: {e}") 

#-------------------------------------------
# С БИБЛИОТЕКАМИ
#-------------------------------------------

import toml
import json
start = time.time()

try:    
    with open('data/timetable.toml', 'r', encoding='utf-8') as inputf:
        data = toml.load(inputf)
    
    with open('data/TIMETABLE.json', 'w', encoding='utf-8') as outputf:
        json.dump(data, outputf, ensure_ascii=False, indent=2)
except Exception as e:
        print(f"Ошибка из index.py: {e}")    
finally:
    print('Время работы c библиотеками: ', (time.time() - start) * 100)

# with open('data/timetalbe.json', 'r', encoding='utf-8') as file1_json:
#         f1 = file1_json.read()
# with open('data/timetalbe.json', 'r', encoding='utf-8') as file2_json:
#         f2 = file2_json.read()
# print(f1 == f2)

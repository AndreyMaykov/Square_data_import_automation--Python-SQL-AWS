def get_nested(dict, key_path):
    # Access a nested dictionary value using the key path.
    # If the path does not exist, return the string 'N/A'. 
    y = dict
    for x in key_path:
        y = y.get(x, 'N/A')
        if y == 'N/A':
            break
    return y

def rev_dict(dict_list, old_key, old_key_path):
    # Create a dictionary new_dict from the list of dictionaries dict_list 
    # by iterating through dict_list. For each dict in dict_list, 
    # a key:value pair of new_dict is created from the values of dict
    # specified by their dict keys and old_key and old_key_path
    new_dict = {}
    for dict in dict_list:             #new_key -- may be a value in old_dict
        new_dict[dict[old_key]] = get_nested(dict, old_key_path)
    return new_dict

def flatten(x):
    y = [num for sublist in x for num in sublist]
    return y


def sql_quotes(x):
    if type(x) == str:
        if x == 'N/A':
            y = 'NULL'
        else:
            y = "\'" + x + "\'"
    else:
        y = str(x)
    return y


def sql_column_names(column_names: list) -> str:
    return ', '.join(map(str, column_names))

def sql_values_row(val: list) -> str: 
    # If val[i] is a string, it becomes "\'"+ val[i] + "\'";
    row = '(' + ', '.join(map(sql_quotes, val)) + ')'
    return row

def cast_as_new(x_str):  
    # 'x_string' -> 'x_string = NEW.x_string'; 
    # required for "upsert" queries
    x_str = x_str + " = NEW." + x_str
    return x_str
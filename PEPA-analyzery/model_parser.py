import re
import json
from typing import List

def remove_comments(input_string: str):
    # Remove /* */ comments
    input_string = re.sub(r'/\*.*?\*/', '', input_string, flags=re.DOTALL)
    
    # Remove // comments
    input_string = re.sub(r'//.*?$\s*', '', input_string, flags=re.MULTILINE)

    return input_string

def remove_tab(input_string: str):
    return re.sub(r'\t', '', input_string) 

def remove_newline(input_string: str):
    return re.sub(r'\n', '', input_string)

def remove_whitespaces(input_string: str):
    return re.sub(r'\s', '', input_string)

def remove_unneeded_characters(input_string: str) -> str:
    """
    Remove unnecessaris characters used to parse the PEPA model as:
    
    - comments;
    - tabs;
    - newline;
    - whitespaces.

    Args:
        input_string (str): line taken from PEPA model file. 

    Returns:
        (str): clean parsed line.  
    """
    input_string = remove_comments(input_string=input_string)
    input_string = remove_tab(input_string=input_string)
    input_string = remove_newline(input_string=input_string)
    input_string = remove_whitespaces(input_string=input_string)
    return input_string

def populate_components(incoming_component: str, components_actions: List[str], components_parsed: dict) -> dict:
    
    if len(components_actions) > 0:
            
        next_state_activity = components_actions[0].split('.')[0].split(',')[0][1:] # Taking activity value
        next_state_rate = components_actions[0].split('.')[0].split(',')[1][:-1] # Taking rate value
        next_state = components_actions[0].split('.')[1] # Taking target component 
        next_step = {'transition': incoming_component + " -> " +  next_state_activity, 'rate': next_state_rate}
        
        if next_state not in components_parsed:
            # If components does not have associated incoming transitions
            components_parsed[next_state] = [next_step]
        else:
            # If components already has associated incoming transitions
            components_parsed[next_state].append(next_step)
        
        # Removing heading action
        components_actions = components_actions[1:]
        populate_components(incoming_component=incoming_component, components_actions=components_actions, components_parsed=components_parsed)
    else:
        return components_parsed
 
def parse_components(component: str, component_value: str, components: dict) -> dict:
    components_actions = component_value.split('+')
    
    populate_components(incoming_component=component, components_actions=components_actions, components_parsed=components) 
     
    return components
    
def parse_model(filePath: str):
    
    try:
        file = open(file=filePath)
    except Exception:
        print(f"File {filePath} may not exists. Make file exists.")
        exit(1)
    
    rows = []
    row = ""
    
    model = { 'rates': [], 'components': {}}
    
    line_to_parse = file.readlines()
    file.close()
    if len(line_to_parse) == 0:
        print(f"No rows in {filePath} to parse.")
        exit(0)
        
    for line in line_to_parse:
        # Remove unnecessaries chars 
        row += remove_unneeded_characters(input_string=line)
        # Avoid empty lines
        if row == '':
            continue
        elif row.find(';') != -1: 
            rows.append(row)
            row = ""
    
    for row in rows:
        row_splitted = row.split('=')
        entity = row_splitted[0] # Rate or Component
        value = row_splitted[1][:-1] # Take value and remove ';' delimiter in tail
        
        if entity[0].islower():
            # Parsing rates  
            model["rates"].append({"rate": entity, "value": value})
        else: 
            # Parsing components 
            parse_components(component=entity, component_value=value, components=model["components"]) 
            
    print(json.dumps(model, sort_keys=True, indent=4)) 
parse_model("/Users/matteo/Documents/Unive/FMFSV/PEPA-analyzery/model.pepa")
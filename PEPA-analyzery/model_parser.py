import re
import json
from typing import List
from itertools import product

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

def populate_components(component: str, components_actions: List[str], components_parsed: dict) -> dict:
    
    if len(components_actions) > 0:
            
        next_state_activity = components_actions[0].split('.')[0].split(',')[0][1:] # Taking activity value
        next_state_rate = components_actions[0].split('.')[0].split(',')[1][:-1] # Taking rate value
        next_state = components_actions[0].split('.')[1] # Taking target component 
        next_step = {'next_state': next_state, 'rate': next_state_rate}
        
        if component not in components_parsed:
            components_parsed[component] = {}
            # If components does not have associated incoming transitions
            if next_state_activity not in components_parsed[component]:
                components_parsed[component][next_state_activity] = [next_step]
            else: 
                components_parsed[component][next_state_activity].append(next_step)
 
        else:
            # If components already has associated incoming transitions
            if next_state_activity not in components_parsed[component]:
                components_parsed[component][next_state_activity] = [next_step]
            else: 
                components_parsed[component][next_state_activity].append(next_step)  
                           
        # Removing heading action
        components_actions = components_actions[1:]
        populate_components(component=component, components_actions=components_actions, components_parsed=components_parsed)
    else:
        return components_parsed
 
def parse_components(component: str, component_value: str, components: dict) -> dict:
    """
    Recursively extract PEPA model components with their relatives transitions in a dictionary

    Args:
        component (str): component's name
        component_value (str): list of all component activities
        components (dict): components dictionary to populate by parsing component's activities
    Returns:
        _type_: _description_
    """
    
    components_actions = component_value.split('+')
    
    populate_components(component=component, components_actions=components_actions, components_parsed=components) 
     
    return components


def compute_outgoing_states(current_state: List[str], activity: str, model: dict):
    """ 
    Compute every outgoing states starting from a `current_sate` and given an `activity`.
    Transitions are followed by using `model` as reference.
    
    Args:
        current_state (List[str]): list of current PEPA components of the system at a given time T.
        activity (str): 
        model (dict): _description_
    """
    component_next_state = []
    is_set_present = False
    for component in current_state:
        if len(model["components"][component][activity]) > 1:
            is_set_present = True
            multiple_states_outcomes = set([outgoing_component_state['next_state'] for outgoing_component_state in model["components"][component][activity]])
            component_next_state.append(multiple_states_outcomes) 
        else: 
            component_next_state.append(model["components"][component][activity][0]["next_state"])
        
    if is_set_present: 
        # Convert to set if not already a set
        sets = [elem if isinstance(elem, set) else {elem} for elem in component_next_state]
        # Calculate combinations
        component_next_state = list(map(lambda x: list(x), list(product(*sets))))
        
    print(activity)
    print(component_next_state)
            
def parse_model(filePath: str) -> dict:
    
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
            
    return model 
    
    

model = parse_model("/Users/matteo/Documents/Unive/FMFSV/PEPA-analyzery/model.pepa")

current_state = ["MUn", "EnvUn", "MF", "EnvF", "MLV", "EnvLV", "C"]
activities = ["mUn", "mEnvU", "mEnvF", "mF", "mLV", "mEnvL", "mFake"]

print(current_state)

for activity in activities:
    compute_outgoing_states(current_state=current_state, activity=activity, model=model)
# print(json.dumps(model, indent=4))
import re
import os 
import json
from typing import List
from itertools import product
import graphviz
import logging
from states import model_states

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

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
    Remove unnecessaries characters used to parse the PEPA model as:
    
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
        Parsed PEPA model dictionary, with `rate` and `components` filed.
    """
    
    components_actions = component_value.split('+')
    
    populate_components(component=component, components_actions=components_actions, components_parsed=components) 
     
    return components


def compute_outgoing_states(current_state: List[str], activity: str, model: dict) -> List[str]:
    """ 
    Compute every outgoing states and their relative rates 
    starting from a `current_state` and given an `activity`.
    Transitions are followed by using `model` as reference.
    
    Args:
        current_state (List[str]): list of current PEPA components of the system at a given time T.
        activity (str): PEPA component's activity for the model.
        model (dict): parsed PEPA model 
    Returns: 
        List of outgoing states from a current state given an activity.
    """
    component_next_state = []
    next_state_rates = []
    multiple_outgoing_states = False
    # If activity does not bring our current_state to a next_state, we do want to ignore it
    is_activity_valid = False
    for component in current_state:
        if activity in model["components"][component]:
            # We now know for sure that the activity is bringing our state in a next one
            is_activity_valid = True
            # If activity produces two or more outgoing states 
            if len(model["components"][component][activity]) > 1:
                multiple_outgoing_states = True
                multiple_state_outcomes = set([outgoing_component_state['next_state'] for outgoing_component_state in model["components"][component][activity]])
                component_next_state.append(multiple_state_outcomes) 
            else: 
                # Transition with exactly one outgoing state
                component_next_state.append(model["components"][component][activity][0]["next_state"])
        else:
            # If no transition exists for this action
            component_next_state.append(component)
            
    if multiple_outgoing_states: 
        # Convert to set and calculate combinations
        sets = [elem if isinstance(elem, set) else {elem} for elem in component_next_state]
        component_next_state = list(map(lambda x: list(x), list(product(*sets))))
    elif not is_activity_valid:
        component_next_state = []
    
    return (component_next_state)

def compute_activities(model: dict) -> List[str]:
    
    """
    Given a model extract all its related activities.
    
    Args:
        model (dict): parsed PEPA model
    """
    activities = set()
    
    # Adding activities from the component
    for component in model["components"]:
        for activity in dict(model["components"][component]).keys():
            activities.add(activity)
    
    # Set to list    
    return [activity for activity in activities]

def parse_model(filePath: str) -> dict:
    
    try:
        file = open(file=filePath)
    except Exception:
        logger.error(f"[MODEL PARSER] - File {filePath} may not exists. Make sure file is present.")
        exit(1)
    
    rows = []
    row = ""
    
    model = { 'rates': [], 'components': {}}
   
    logger.debug(f"[MODEL PARSER] - Parsing model for PEPA model {filePath} ... ") 
    line_to_parse = file.readlines()
    file.close()
    if len(line_to_parse) == 0:
        logger.error(f"[MODEL PARSER] - No rows in {filePath} to parse.")
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
    
    # Writing model to file for debug purposes
    parsed_model = open(file='parsed_model.json', mode='w')
    parsed_model.write(json.dumps(obj=model,indent=4))
    parsed_model.close()
    logger.debug(f"[MODEL PARSER] - Parsing model operation completed. Complete file can be found in \"{os.getcwd()}parsed_mode.json\"") 
    
    return model

def draw_derivation_graph(model: str, activities: List[str]):
    graph = graphviz.Digraph('Derivation graph', format='svg')
    graph.attr(rankdir='TB') 
    graph.attr(nodesep='2.0')
    graph.attr(ranksep='2.0')

    # Looping over model different model states
    for current_state in model_states:
        
        # Turning current PEPA state in a representable format
        current_state_graph = "(" + ", ".join(current_state) + ")"
        # Creating node for starting state
        graph.node(current_state_graph)
        
        logger.debug("[+] -------------------------------------------------------------------------------------------------------------------------------------- [+]")
        logger.debug(f"[MODEL PARSER] - Computing outgoing states for state {current_state_graph}")
        
        # Looping over different activities
        for activity in activities:
            logger.debug(f"[MODEL PARSER] --> Analyzing transition {activity}")
            outgoing_states = compute_outgoing_states(current_state=current_state, activity=activity, model=model)
            
            multiple_outgoing_states = isinstance(outgoing_states, List) and len(outgoing_states) > 1 and isinstance(outgoing_states[0], List)
            single_outgoing_state = isinstance(outgoing_states, List) and len(outgoing_states) == 1
            # Transition for current_state produces multiple outgoing states
            if multiple_outgoing_states:
                # Looping on outgoing state given: current state -> activity
                for outgoing_state in outgoing_states:
                    outgoing_state_string = "(" + ", ".join(outgoing_state) + ")"
                    graph.node(outgoing_state_string)
                    graph.edge(current_state_graph, outgoing_state_string, activity)
            # Transition produces exactly one state
            elif single_outgoing_state: 
                graph.node(outgoing_state_string)
                graph.edge(current_state_graph, outgoing_state_string, activity)
            
    graph.render('derivation_graph', cleanup=True, format='svg')



import re
import os 
import json
from typing import List
from itertools import product
import graphviz
import logging
from states import model_states, ctmc_states

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

def check_passive_rate(next_rate: str) -> bool:
    """
    Return true if passive component is contained in rate.
    
    Args:
        next_rate (str): next action rate for component in PEPA model

    Returns:
        (bool) True if `next_rate` is a passive rate, False otherwise.
    """
    return "T" in next_rate

def compute_outgoing_rates(model: dict, component: str, activity: str, multiple: bool) -> List[str]:
    
    """
    Computes and returns a list of outgoing rates for a given component and activity in a model.

    Args:
        model (dict): The model containing information about components and their activities.
        component (str): The specific component in the model for which outgoing rates are to be computed.
        activity (str): The activity within the specified component for which outgoing rates are to be computed.
        multiple (bool): A flag indicating whether there are multiple outgoing states for the given activity.

    Returns:
        List[str]: A list containing outgoing rates for the specified component and activity. 
                    If `multiple` is False, the list will contain a single rate.

    Note:
    - If `multiple` is False, the function retrieves the rate directly from the model.
    - If `multiple` is True, the function iterates through multiple outgoing states and 
      adds the rates to the list, excluding passive rates as determined by the `check_passive_rate` function.

    """
    
    
    next_rates = list()
    if not multiple: 
        rate = model["components"][component][activity][0]["rate"]
        
        if not check_passive_rate(next_rate=rate): 
            next_rates.append(rate)

    else: 
        outgoing_states = model["components"][component][activity]
        for next_component in outgoing_states:
            rate = next_component["rate"]
            
            # Adding all rates for non passive rates
            if not check_passive_rate(next_rate=rate):
                next_rates.append(rate)
                
    return next_rates
        
        

def compute_outgoing_states(current_state: List[str], activity: str, model: dict) -> (List[str], List[str]):
    
    """ 
    Compute every outgoing states and their relative rates 
    starting from a `current_state` and given an `activity`.
    Transitions are followed by using `model` as reference.
    
    When looking for an activity rate, we want to check 
    that component performing the activity with a defined rate.
    Args:
        current_state (List[str]): list of current PEPA components of the system at a given time T.
        activity (str): PEPA component's activity for the model.
        model (dict): parsed PEPA model 
    Returns: 
        List of outgoing states from a current state given an activity with their rates.
    """
    
    component_next_state = []
    next_state_rates = []
    outgoing_rates = []
    multiple_outgoing_states = False
    # If activity does not bring our current_state to a next_state, we do want to ignore it
    is_activity_valid = False
    for component in current_state:
        if activity in model["components"][component]:
            is_activity_valid = True
            # If activity produces two or more outgoing states 
            if len(model["components"][component][activity]) > 1:
                multiple_outgoing_states = True
                multiple_state_outcomes = set([outgoing_component_state['next_state'] for outgoing_component_state in model["components"][component][activity]])
                component_next_state.append(multiple_state_outcomes) 
                outgoing_rates = compute_outgoing_rates(model=model, component=component, activity=activity, multiple=True)
            else: 
                # Transition with exactly one outgoing state
                component_next_state.append(model["components"][component][activity][0]["next_state"])
                outgoing_rates = compute_outgoing_rates(model=model, component=component, activity=activity, multiple=False)
            
            # Add rates for single or multiple 
            next_state_rates = next_state_rates + outgoing_rates
        
        else:
            # If no transition exists for this action
            component_next_state.append(component)
            
    if multiple_outgoing_states: 
        # Convert to set and calculate combinations
        sets = [elem if isinstance(elem, set) else {elem} for elem in component_next_state]
        component_next_state = list(map(lambda x: list(x), list(product(*sets))))
    elif not is_activity_valid:
        component_next_state = []
        next_state_rates = []
    
    return (component_next_state, next_state_rates)

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
      
    return [activity for activity in activities]

def parse_model(filePath: str) -> dict:
    
    """
    Given a model in PEPA format, convert into a dict format where 
    `rate` and `components` are present.
    
    Args:
        filepath (str): string containig the path where the provided model.pepa is supplied
    Returns:
    """ 
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

def convert_ctmc_to_graph(ctmc: dict):
    
    """
    Converts a Continuous-Time Markov Chain (CTMC) represented as a dictionary into a graph and saves it as an image.

    Args:
        ctmc (dict): A dictionary representing the CTMC where keys are components and values are dictionaries
                  with outgoing states and corresponding rates.

    Returns:
        None: The function generates a graph and saves it as an image.

    Note:
    - The function uses the Graphviz library to create and render the graph.
    """
    
    graph = graphviz.Digraph('CTMC graph', format='png')
    graph.attr(rankdir='TB') 
    graph.attr(nodesep='1.4')
    graph.attr(ranksep='1.5')
    
    for component, outgoing_state in ctmc.items():
        graph.node(component)
        for state, rate in outgoing_state.items():
            # Skip reflective edges
            if component != state:
                graph.edge(component, state, rate)
    
    logger.info(f"[MODEL PARSER] - Drawning CTMC graph in \"{os.getcwd()}/ctmc_graph.svg\"... ")           
    graph.render('ctmc_graph', cleanup=True, format='png')
    logger.info(f"[MODEL PARSER] - CTMC graph correctly rendered.") 
    
def compact_ctmc_rates(ctmc: dict) -> dict:
    
    """
    Build up a CTMC with all the aggregated rates present in the derivation graph.
    
    Args: 
        ctmc (dict): continuous time markov chain obtained from PEPA model
    Returns: 
        (dict) ctmc with aggregated rates
    """
    
    for component, outgoing_state in ctmc.items():
        for state, rate in outgoing_state.items():
            # We take only the first element as there can be multiple rate with the same value
            ctmc[component][state] = min(rate, key=len)
    
    return ctmc

def draw_infinitesimal_generator_matrix(ctmc: dict):
    
    """
    Generate a infinitesimal generator matrix for a given CTMC.
    
    Args: 
        ctmc (dict): continuous time markov chain obtained from PEPA model
    Returns: 
        (dict) m x m matrix where m are the number of states.
        Every entry contains the transitional probability from one state to another.
    """
    
    m = len(ctmc_states.keys())
    Q = [["0"] * m for _ in range(m)]
    
    for i in range(1, m + 1):
        total_rate = ""
        for j in range(1, m + 1):
            # No self-edges are considerated
            if i != j:
                try:
                    Q[i - 1][j - 1] = ctmc[str(i)][str(j)]
                    if total_rate != "":
                        total_rate += " + "
                    total_rate += ctmc[str(i)][str(j)]
                except Exception:
                    pass
        if total_rate != "":
            Q[i - 1][i - 1] = "- (" + total_rate + ")"  

    # TODO: draw the matrix in some way and then make it return the matrix Q from the function
    for row in Q:
        for element in row:
            print(element, end='\t')
        print('\n')
    
def draw_CTMC_graph(model: dict, activities: List[str]):
    
    """
    Draw the Continuous Time Markov Chain graph given a parsed PEPA model.
    
    Args:
        model (dict): parsed PEPA model.
        activities (List[str]): list of activies performed by the model.
    
    """
    
    ctmc = {}
    for _, value in ctmc_states.items():
        ctmc[value] = {}
    
    # Looping over model different model states
    for current_state in model_states:
        
        # Turning current PEPA state in a representable format
        current_state_graph = "(" + ", ".join(current_state) + ")"
        try:
            current_state_number = ctmc_states[current_state_graph]
        except KeyError as e:
            logger.error(f"[MODEL PARSER] - Unmatched model state {current_state_graph}")
   
        logger.debug("[+] -------------------------------------------------------------------------------------------------------------------------------------- [+]")
        logger.debug(f"[MODEL PARSER] - Computing outgoing states for state {current_state_graph}")
             
        # Looping over different activities
        for activity in activities:
            logger.debug(f"[MODEL PARSER] --> Analyzing transition {activity}")
            outgoing_states, outgoing_rates = compute_outgoing_states(current_state=current_state, activity=activity, model=model)
            
            # If state has changed
            if len(outgoing_rates) > 0:    
                multiple_outgoing_states = isinstance(outgoing_states, List) and len(outgoing_states) > 1 and isinstance(outgoing_states[0], List)
                single_outgoing_state = isinstance(outgoing_states, List)
                outgoing_state_string = ""
                try:
                    # Transition for current_state produces multiple outgoing states
                    if multiple_outgoing_states:
                        # Looping on outgoing state given: current state -> activity
                        for outgoing_state in enumerate(outgoing_states):
                            outgoing_state_string = "(" + ", ".join(outgoing_state) + ")"
                            outgoing_state_number = ctmc_states[outgoing_state_string]
                            if current_state_number != outgoing_state_number:
                                if outgoing_state_number not in ctmc[current_state_number]:
                                    ctmc[current_state_number][outgoing_state_number] = []
                                ctmc[current_state_number][outgoing_state_number] = list(ctmc[current_state_number][outgoing_state_number]).append(outgoing_rates)
                                                                
                    # Transition produces exactly one state
                    elif single_outgoing_state: 
                        outgoing_state_string = "(" + ", ".join(outgoing_states) + ")"
                        outgoing_state_number = ctmc_states[outgoing_state_string]                        
                        if outgoing_state_number not in ctmc[current_state_number]:
                            ctmc[current_state_number][outgoing_state_number] = outgoing_rates
                        else:
                            ctmc[current_state_number][outgoing_state_number] = list(ctmc[current_state_number][outgoing_state_number]) + outgoing_rates
                except KeyError as e:
                    logger.error(f"[MODEL PARSER] - Unmatched model state {outgoing_state_string}")
    
    ctmc = compact_ctmc_rates(ctmc=ctmc)
    convert_ctmc_to_graph(ctmc=ctmc)
    
    draw_infinitesimal_generator_matrix(ctmc=ctmc)

def draw_derivation_graph(model: str, activities: List[str]):
    
    """
    Draw the derivation graph given a parsed PEPA model.
    
    Args:
        model (dict): parsed PEPA model.
        activities (List[str]): list of activies performed by the model.
        
    """
    
    graph = graphviz.Digraph('Derivation graph', format='png')
    graph.attr(rankdir='TB') 
    graph.attr(nodesep='1.4')
    graph.attr(ranksep='1.5')
    
    # Looping over model different model states
    for current_state in model_states:
        
        # Remove state number information
        current_state = current_state[1:]
        # Turning current PEPA state in a representable format
        current_state_graph = "(" + ", ".join(current_state) + ")"
        # Creating node for starting state
        graph.node(current_state_graph)
        
        logger.debug("[+] -------------------------------------------------------------------------------------------------------------------------------------- [+]")
        logger.debug(f"[MODEL PARSER] - Computing outgoing states for state {current_state_graph}")
             
        # Looping over different activities
        for activity in activities:
            logger.debug(f"[MODEL PARSER] --> Analyzing transition {activity}")
            outgoing_states, outgoing_rates = compute_outgoing_states(current_state=current_state, activity=activity, model=model)
            
            # If state has changed
            if len(outgoing_rates) > 0:    
                multiple_outgoing_states = isinstance(outgoing_states, List) and len(outgoing_states) > 1 and isinstance(outgoing_states[0], List)
                single_outgoing_state = isinstance(outgoing_states, List)
                # Transition for current_state produces multiple outgoing states
                if multiple_outgoing_states:
                    # Looping on outgoing state given: current state -> activity
                    for i, outgoing_state in enumerate(outgoing_states):
                        outgoing_state_string = "(" + ", ".join(outgoing_state) + ")"
                        # graph.node(outgoing_state_string)
                        graph.edge(current_state_graph, outgoing_state_string, f"({activity}, {outgoing_rates[i % len(outgoing_rates)] if len(outgoing_rates) > 1 else outgoing_rates[0]})")
                            
                # Transition produces exactly one state
                elif single_outgoing_state: 
                    outgoing_state_string = "(" + ", ".join(outgoing_states) + ")"
                    # graph.node(outgoing_state_string)
                    graph.edge(current_state_graph, outgoing_state_string, f"({activity}, {outgoing_rates[0]})")
    logger.info(f"[MODEL PARSER] - Drawning derivation graph in \"{os.getcwd()}/derivation_graph.svg\"... ")           
    graph.render('derivation_graph', cleanup=True, format='png')
    logger.info(f"[MODEL PARSER] - Derivation graph correctly rendered.")           



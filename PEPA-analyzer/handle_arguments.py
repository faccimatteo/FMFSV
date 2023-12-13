import argparse 
import logging 
import os 

logger = logging.getLogger("")
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

def parse_model_argument():
    parser = argparse.ArgumentParser(description='Parse the --model or -m argument.')
    
    parser.add_argument('--model', '-m', required=True, help='PEPA model path.')

    try:
        # Parsa gli argomenti da linea di comando
        args = parser.parse_args()
        # If relative path turn it to absolute
        model_path = os.path.abspath(args.model)
        # Restituisci il valore dell'argomento --model o -m
        return args.model

    except argparse.ArgumentError as e:
        logger.error(f"[MODEL PARSER] - Missing model path parameter value. Specify it with the parameter -m or --module.")
        exit(1)
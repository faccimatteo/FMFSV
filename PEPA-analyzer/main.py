import sys 
from PEPA_parser import parse_model, draw_derivation_graph, compute_activities, draw_CTMC_graph
from handle_arguments import parse_model_argument

def main():
    modelPath = parse_model_argument()
    model = parse_model(filePath=modelPath)
    activities = compute_activities(model=model)

    draw_derivation_graph(model=model, activities=activities)
    # draw_CTMC_graph(model=model, activities=activities)

if __name__ == "__main__":
    main()
from PEPA_parser import parse_model, draw_derivation_graph, compute_activities

def main():
    model = parse_model("/Users/matteo/Documents/Unive/FMFSV/PEPA-analyzer/moadel.pepa")
    # activities = ["mUn", "mEnvU", "mEnvF", "mF", "mLV", "mEnvL", "mFake"]
    activities = compute_activities(model=model)

    draw_derivation_graph(model=model, activities=activities)
    

if __name__ == "__main__":
    main()
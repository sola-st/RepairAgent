import os

import argparse

def main(start_exp, end_exp):
    print(f"Start experiment number: {start_exp}")
    print(f"End experiment number: {end_exp}")
    patches = {}
    patches_list = []
    detailed_fixed_mutation = []
    for i in range(start_exp, end_exp, 1):
        patches[i] = []
        if os.path.exists("experiment_{}".format(i)):
            if os.path.exists(os.path.join("experiment_{}".format(i), "plausible_patches")):
                patches[i] = patches[i] + os.listdir(os.path.join("experiment_{}".format(i), "plausible_patches"))
                patches_list += [f.replace("plausible_patches_", "").replace(".json", "").replace("_", " ") for f in os.listdir(os.path.join("experiment_{}".format(i), "plausible_patches"))]
                for f in os.listdir(os.path.join("experiment_{}".format(i), "plausible_patches")):
                    os.system("cp {} {}".format(os.path.join("experiment_{}".format(i), "plausible_patches", f), "all_plausibles/{}_{}".format(i, f)))
                detailed_fixed_mutation.extend(["experiment_{} ".format(i)+p for p in [f.replace("plausible_patches_", "").replace(".json", "").replace("_", " ") for f in os.listdir(os.path.join("experiment_{}".format(i), "plausible_patches"))]])
    print("\n".join(list(set(patches_list))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the start and end experiment numbers.")
    parser.add_argument("start_exp", type=int, help="The start experiment number.")
    parser.add_argument("end_exp", type=int, help="The end experiment number.")

    args = parser.parse_args()
    start_exp = args.start_exp
    end_exp = args.end_exp

    main(start_exp, end_exp)



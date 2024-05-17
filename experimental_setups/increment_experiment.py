import os

with open("experimental_setups/experiments_list.txt", "r+") as expl:
    exps = expl.read().splitlines()
    #print(exps)
    if exps:
        last_exp = int(exps[-1].split("_")[1])
    else:
        last_exp = 0

    print("Creating experiment folder:", last_exp+1)
    expl.write("experiment_{}\n".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/logs".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/responses".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/external_fixes".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/saved_contexts".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/mutations_history".format(last_exp + 1))
    os.mkdir("experimental_setups/experiment_{}/plausible_patches".format(last_exp + 1))
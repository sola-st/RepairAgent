import os

base_dir = "defects4j/framework/projects/"

def get_list_of_projects(path="defects4j/framework/projects"):
    dirs = os.listdir(path)
    projects = []
    for d in dirs:
        if os.path.isdir(os.path.join(path, d)) and d!="lib":
            projects.append(d)
    return projects


def get_list_of_bugs(project_path):
    patches = [p.split(".")[0] for p in os.listdir(os.path.join(project_path, "patches")) if "src" in p]
    return patches


projects = get_list_of_projects()
bugs_list = []
for p in projects:
    project_path = os.path.join(base_dir, p)
    bugs = get_list_of_bugs(project_path)
    for b in bugs:
        bugs_list.append((p, b))

print(len(bugs_list))

with open("chatrepair_list.txt") as crlt:
    chatrepair_list = crlt.read()

chatrepair_list = chatrepair_list.split(",")
chatrepair_list = [tuple(c.split("_")) for c in chatrepair_list]

bugs_list = [" ".join(c) for c in bugs_list]

with open("experimental_setups/fixed_so_far") as fsf:
    fixed_so_far = fsf.read().splitlines()

with open("experimental_setups/pairs_output.txt") as pot:
    pairs_output = pot.read().splitlines()


deprecated = ["Cli 6", "Closure 63", "Closure 93", "Collections 1", "Collections 2", "Collections 3", "Collections 4",
"Collections 5", "Collections 10", "Collections 15", "Collections 20",
"Collections 6", "Collections 11", "Collections 16", "Collections 21",
"Collections 7", "Collections 12", "Collections 17", "Collections 22",
"Collections 8", "Collections 13", "Collections 18", "Collections 23",
"Collections 9", "Collections 14", "Collections 19", "Collections 24",
"Lang 2", "Mockito 21"]

with open("experimental_setups/error_excludes") as eex:
    erronous_ones = eex.read().splitlines()

print("Finished:", len(set(fixed_so_far+pairs_output+deprecated)- set(erronous_ones)))
print("Full set:", len(set(bugs_list)))

print(len(set(bugs_list)-set(fixed_so_far+pairs_output+deprecated)))

batch_start = 118
def construct_batches_files(dir_to_save, bugs_list, excludes, batch_size=5, batches_number = 72):
    filtered_list = [b for b in bugs_list if b not in excludes]
    chunks = [filtered_list[i:i+batch_size] for i in range(0, len(filtered_list), batch_size)]
    for i, chunk in enumerate(chunks):
        with open(os.path.join(dir_to_save, str(i + batch_start)), "w") as svfile:
            svfile.write("\n\n".join(chunk))

construct_batches_files("experimental_setups/batches", bugs_list, set(fixed_so_far+pairs_output+deprecated)-set(erronous_ones))
import os
import argparse
import shutil

def main(start_exp, end_exp):
    """
    Collect plausible patches from experiment directories.
    
    Args:
        start_exp: Starting experiment number (inclusive)
        end_exp: Ending experiment number (exclusive)
    """
    print(f"Start experiment number: {start_exp}")
    print(f"End experiment number: {end_exp}")
    
    patches = {}
    patches_list = []
    detailed_fixed_items = []
    
    # Directories to check for plausible patches
    patch_directories = ["plausible_patches", "external_fixes"]
    
    for i in range(start_exp, end_exp, 1):
        patches[i] = []
        if os.path.exists("experiment_{}".format(i)):
            # Process each patch directory
            for patch_dir in patch_directories:
                dir_path = os.path.join("experiment_{}".format(i), patch_dir)
                if os.path.exists(dir_path):
                    # Get list of files in this directory
                    patch_files = os.listdir(dir_path)
                    if not patch_files:
                        continue
                        
                    patches[i] = patches[i] + patch_files
                    
                    # Process files based on their directory
                    if patch_dir == "plausible_patches":
                        # Process mutation-based patches
                        processed_names = [f.replace("plausible_patches_", "").replace(".json", "").replace("_", " ") for f in patch_files]
                        patches_list += processed_names
                        
                        # Copy files to all_plausibles directory
                        for f in patch_files:
                            source = os.path.join(dir_path, f)
                            dest = os.path.join("all_plausibles", f"{i}_{f}")
                            shutil.copy2(source, dest)
                            
                        detailed_fixed_items.extend([f"experiment_{i} {p}" for p in processed_names])
                    
                    elif patch_dir == "external_fixes":
                        # Process external fixes
                        for f in patch_files:
                            # Copy files to all_plausibles directory with prefix to indicate source
                            source = os.path.join(dir_path, f)
                            dest = os.path.join("all_plausibles", f"external_{i}_{f}")
                            shutil.copy2(source, dest)
                            
                            # Add to patches list with indication this is an external fix
                            name = f.replace(".json", "").replace("_", " ")
                            patches_list.append(f"[External] {name}")
                            detailed_fixed_items.append(f"experiment_{i} [External] {name}")
    
    # Print unique patch identifiers
    print("\n".join(list(set(patches_list))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set the start and end experiment numbers.")
    parser.add_argument("start_exp", type=int, help="The start experiment number.")
    parser.add_argument("end_exp", type=int, help="The end experiment number.")

    args = parser.parse_args()
    start_exp = args.start_exp
    end_exp = args.end_exp

    if not os.path.exists("all_plausibles"):
        os.mkdir("all_plausibles")

    main(start_exp, end_exp)



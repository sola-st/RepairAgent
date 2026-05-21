#!/bin/bash
export PATH=$PATH:/workspaces/RepairAgent/repair_agent/defects4j/framework/bin
export PERL5LIB=/home/vscode/perl5/lib/perl5:$PERL5LIB
CHECKOUT_DIR="/workspaces/RepairAgent/researchAnalysis/checkouts"

checkout_bug() {
    local bug=$1
    local project=$(echo $bug | cut -d_ -f1)
    local id=$(echo $bug | cut -d_ -f2)
    local target_dir="${CHECKOUT_DIR}/${bug}_fixed"
    
    if [ -d "$target_dir" ]; then
        echo "SKIP: $bug (already exists)"
        return 0
    fi
    
    echo "Checking out: $project $id fixed..."
    defects4j checkout -p $project -v ${id}f -w "$target_dir" 2>&1 | tail -1
    echo "DONE: $bug"
}

# Run checkouts - pass bug list as args
for bug in "$@"; do
    checkout_bug "$bug"
done

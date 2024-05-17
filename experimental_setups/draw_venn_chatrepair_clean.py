from matplotlib import pyplot as plt
from venn import venn
import pandas


chatgpt_fixes = """Lang-59
Lang-45
Closure-44
Lang-28
Math-69
Lang-16
Chart-9
Math-85
Chart-17
Closure-83
Chart-12
Math-94
Closure-70
Closure-73
Time-4
Lang-11
Closure-10
Closure-36
Mockito-34
Closure-5
Math-82
Math-27
Closure-97
Math-59
Time-16
Chart-11
Closure-124
Closure-92
Lang-21
Chart-7
Math-58
Chart-1
Chart-13
Math-56
Math-89
Closure-61
Lang-57
Lang-40
Chart-5
Lang-44
Closure-101
Lang-24
Math-91
Math-45
Lang-29
Math-3
Closure-57
Closure-119
Math-106
Closure-38
Closure-11
Closure-77
Closure-20
Math-41
Chart-10
Chart-26
Lang-55
Closure-67
Math-34
Math-11
Closure-52
Closure-19
Mockito-38
Lang-39
Chart-8
Math-95
Closure-33
Closure-102
Closure-65
Closure-128
Closure-62
Lang-43
Lang-52
Time-15
Math-73
Closure-125
Closure-2
Math-70
Mockito-12
Chart-6
Closure-56
Math-5
Math-57
Closure-13
Lang-26
Math-50
Math-96
Closure-78
Math-79
Lang-33
Math-33
Lang-38
Math-53
Lang-27
Closure-31
Chart-20
Mockito-29
Chart-24
Math-2
Math-30
Closure-126
Closure-104
Mockito-24
Closure-86
Math-10
Lang-51
Mockito-22
Lang-61
Closure-18
Math-105
Math-72
Math-80
Chart-4
Closure-15
Cli-11.java
Cli-17.java
Cli-28.java
Cli-40.java
Cli-8.java
Codec-10.java
Codec-17.java
Codec-18.java
Codec-2.java
Codec-3.java
Codec-4.java
Codec-7.java
Codec-9.java
Compress-19.java
Compress-23.java
Csv-11.java
Csv-1.java
Csv-4.java
Gson-11.java
Gson-13.java
Gson-15.java
JacksonCore-25.java
JacksonCore-5.java
JacksonCore-8.java
JacksonDatabind-16.java
JacksonDatabind-1.java
JacksonDatabind-27.java
JacksonDatabind-46.java
JacksonDatabind-57.java
JacksonDatabind-82.java
JacksonDatabind-96.java
JacksonDatabind-97.java
JacksonDatabind-99.java
JacksonXml-5.java
Jsoup-32.java
Jsoup-33.java
Jsoup-34.java
Jsoup-43.java
Jsoup-45.java
Jsoup-46.java
Jsoup-47.java
Jsoup-55.java
Jsoup-57.java
Jsoup-61.java
Jsoup-62.java
Jsoup-77.java
Jsoup-86.java
Jsoup-88.java"""

codex_fixes = """Chart-1
Chart-11
Chart-12
Chart-20
Chart-24
Closure-109
Closure-11
Closure-123
Closure-124
Closure-126
Closure-129
Closure-18
Closure-19
Closure-20
Closure-31
Closure-33
Closure-36
Closure-5
Closure-57
Closure-61
Closure-62
Closure-86
Closure-92
Closure-97
Lang-11
Lang-21
Lang-24
Lang-26
Lang-28
Lang-29
Lang-40
Lang-43
Lang-45
Lang-55
Lang-61
Math-10
Math-11
Math-3
Math-30
Math-33
Math-34
Math-41
Math-5
Math-50
Math-56
Math-57
Math-58
Math-63
Math-69
Math-70
Math-75
Math-80
Math-82
Math-85
Math-91
Math-94
Math-96
Mockito-12
Mockito-24
Time-4
Lang-33
Math-101
Chart-1
Chart-10
Chart-11
Chart-20
Chart-24
Chart-4
Chart-7
Chart-8
Closure-102
Closure-109
Closure-11
Closure-114
Closure-124
Closure-129
Closure-13
Closure-2
Closure-36
Closure-44
Closure-55
Closure-56
Closure-61
Closure-62
Closure-78
Closure-97
Lang-10
Lang-11
Lang-12
Lang-21
Lang-28
Lang-33
Lang-37
Lang-40
Lang-43
Lang-53
Lang-54
Lang-55
Lang-59
Lang-65
Math-10
Math-11
Math-2
Math-27
Math-30
Math-33
Math-34
Math-5
Math-56
Math-57
Math-59
Math-70
Math-73
Math-82
Math-89
Math-91
Math-95
Mockito-12
Mockito-24
Mockito-29
Mockito-33
Mockito-34
Mockito-38
Time-15
Time-27
Chart-11
Chart-12
Chart-20
Closure-123
Closure-18
Closure-31
Closure-57
Closure-62
Closure-70
Closure-73
Closure-77
Closure-86
Lang-21
Lang-24
Lang-33
Lang-38
Lang-43
Lang-51
Lang-57
Lang-61
Math-10
Math-33
Math-34
Math-41
Math-5
Math-58
Math-63
Math-69
Math-82
Math-85
Math-96
Mockito-24"""


def load_selfapr_patches():
    with open("selfAPR.txt", "r") as f:
        s = f.read()
    bugs = s.split(",")
    bugs = [b.replace("_", "-") for b in bugs]
    dfj_12_bug = [b for b in bugs if check_d4j_2(b)]
    dfj_2_bug = [b for b in bugs if check_d4j_2(b, True)]

    return dfj_12_bug, dfj_2_bug


def check_d4j_2(bug, d4j_2=False):
    is_d4j_2 = True
    if 'Time' in bug or 'Math' in bug or 'Mockito' in bug or 'Chart' in bug or 'Lang' in bug:
        is_d4j_2 = False
    elif 'Closure' in bug:
        if int(bug.split(".java")[0].split("-")[-1]) <= 133:
            is_d4j_2 = False

    return is_d4j_2 == d4j_2


def _load_select_baselines_d4j(models):
    dl_methods = ["AlphaRepair", "CURE", "CoCoNuT", "CURE", "Recoder", "SEQUENCER", "DLFix", "RewardRepair"]
    trad_methods = ["Tbar-68", "Prapr2", "AVATAR", "SimFix", "FixMiner", "capgen", "jaid", "sketchfix", "Nopol",
                    "GenProg-A", "jGenProg", "jKali", "jMutRepair", "Kali-A"]
    data = pandas.read_csv("d4j12.csv", header=0)
    toolBugSet = {}
    toolBugSet['Other'] = set()
    for col in data.columns:
        if col in models:
            toolBugSet[col] = (set([x.split("(")[0].replace("_", "-").replace(" ", "-") for x in
                                    data[col].dropna().tolist()]) - {"Lang-2", "Time-21", "Closure-63", "Closure-93"})
        elif col in trad_methods or col in dl_methods:
            toolBugSet["Other"] |= (set([x.split("(")[0].replace("_", "-").replace(" ", "-") for x in
                                    data[col].dropna().tolist()]) - {"Lang-2", "Time-21", "Closure-63", "Closure-93"})

    return toolBugSet

iterlist = """Chart 1
Chart 11
Chart 12
Chart 16
Chart 19
Chart 20
Chart 24
Chart 7
Chart 8
Chart 9
Cli 11
Cli 17
Cli 27
Cli 34
Cli 5
Cli 8
Closure 10
Closure 104
Closure 113
Closure 115
Closure 123
Closure 126
Closure 131
Closure 38
Closure 4
Closure 46
Closure 56
Closure 57
Closure 62
Closure 63
Closure 73
Closure 79
Closure 86
Closure 92
Codec 1
Codec 3
Codec 7
Compress 19
Compress 25
Compress 27
Compress 31
Csv 4
Csv 6
JacksonCore 12
JacksonCore 25
JacksonCore 6
Lang 26
Lang 34
Lang 43
Lang 47
Lang 51
Lang 55
Lang 57
Lang 59
Lang 6
Time 19
Time 4"""

iterlist = iterlist.split("\n")


with open("fixed_so_far") as fsf:
    repair_agent = fsf.read().splitlines()

import matplotlib.pyplot as plt
#from matplotlib_venn import venn

def graph_uniqueness():
    toolBugSet = _load_select_baselines_d4j([])
    dfj_12_bug, dfj_2_bug = load_selfapr_patches()
    #toolBugSet['Other'] |= set(dfj_12_bug)
    toolBugSet['SelfAPR'] = set(dfj_12_bug) | set(dfj_2_bug)
    #toolBugSet['Other'] |= set([x.strip() for x in codex_fixes.splitlines()])
    del toolBugSet['Other']
    toolBugSet['ChatRepair'] = set([x.split(".")[0].strip() for x in chatgpt_fixes.splitlines()])
    toolBugSet['ITER'] = set([c.replace(" ", "-") for c in iterlist])
    toolBugSet['RepairAgent'] = set([c.replace(" ", "-") for c in repair_agent])
    plt.figure()
    plt.tight_layout()
    venn(toolBugSet, fontsize=18, legend_loc="lower left")

    # Increase font size
    #plt.title("Venn Diagram", fontsize=18)  # Example title with fontsize 18
    plt.tight_layout()
    #plt.show()
    plt.savefig("venn_diagram.png")
    print(len(dfj_12_bug), len(dfj_2_bug))

graph_uniqueness()
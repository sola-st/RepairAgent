from prettytable import PrettyTable
import re

self_apr = """Lang 29

Math 30

Math 79

Collections 26

Math 57

Chart 1

Closure 168

Closure 38

Closure 62

Closure 73

Math 82

Math 85

Time 19

JacksonCore 5

Compress 19

JacksonCore 25

JacksonDatabind 17

Closure 40

Closure 70

Closure 86

Math 104

Math 11

Math 22

Math 80

Mockito 26

Cli 8

Codec 16

Codec 3

Codec 4

Codec 7

Codec 9

Compress 23

Jsoup 17

Lang 26

Chart 11

Chart 20

Chart 7

Chart 8

Lang 21

Lang 59

Lang 6

Math 72

JacksonDatabind 34

Jsoup 41

Math 33

Math 46

Math 5

JacksonDatabind 27

Chart 9

Closure 10

Closure 104

Closure 11

Closure 113

Closure 125

Closure 18

Closure 57

Lang 58

Math 94

Cli 12

Compress 38

JxPath 12

Math 32

Compress 27

Compress 27

Codec 8

Closure 92

Math 70

Math 75

Cli 27

Jsoup 24

Jsoup 40

Jsoup 62

Lang 33

Math 59

Cli 25

Cli 28

Cli 37

Codec 17

Compress 14

Csv 4

Gson 6

Jsoup 68

Closure 123

Lang 57

Mockito 5

Time 7

Cli 40

Compress 32

JacksonCore 8

JacksonDatabind 57

JacksonXml 5

Math 41

Math 49

JacksonDatabind 83

Closure 126

Closure 46

Closure 6

JacksonDatabind 102

Math 50

Chart 24

Closure 79

Lang 51

JacksonDatabind 46

JacksonDatabind 99

Mockito 29

Lang 45

Math 73

Time 15

Cli 17

Codec 2""".replace("\n\n", "\n")

#ChatRepair
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
Jsoup-88.java""".replace(".java", "").replace("-", " ")

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

repair_agent_list = """Closure 101
Csv 4
Cli 40
Math 80
Chart 8
Compress 46
Mockito 1
Math 101
Chart 5
Compress 23
Math 94
Lang 49
Cli 8
Math 89
Closure 40
Compress 27
Math 72
Chart 11
Jsoup 1
Lang 44
Csv 14
Cli 11
Closure 6
Jsoup 17
Math 33
Chart 24
Cli 25
Lang 57
Closure 62
Mockito 26
Lang 58
Math 22
Closure 123
Codec 17
JacksonDatabind 101
Closure 115
Gson 15
Lang 24
JacksonCore 25
Closure 152
Jsoup 25
Closure 46
Chart 1
JacksonCore 8
Lang 55
Math 96
Compress 1
Jsoup 40
Math 32
Csv 11
Compress 19
Math 104
Codec 9
Math 82
Lang 10
Closure 92
Jsoup 16
Codec 7
Mockito 38
Closure 10
Math 46
Cli 32
Math 2
Math 70
JacksonDatabind 99
Jsoup 51
Math 91
Mockito 5
Closure 122
Time 19
JacksonCore 4
Jsoup 24
Jsoup 41
Closure 38
Lang 59
Closure 31
Lang 29
Math 57
Lang 60
Csv 2
JacksonXml 5
Math 65
Math 73
JacksonDatabind 41
Lang 14
Mockito 29
Closure 126
Math 34
Chart 9
Closure 18
Lang 20
Jsoup 68
Chart 13
Codec 3
JacksonDatabind 83
Codec 18
Math 27
Lang 33
Csv 8
JacksonCore 14
Jsoup 90
Closure 11
Jsoup 43
Math 85
Closure 78
Closure 65
Math 56
Collections 26
Codec 8
Compress 13
JacksonDatabind 34
Lang 21
Lang 16
Closure 70
Closure 168
Jsoup 33
JacksonDatabind 102
Closure 73
JacksonCore 5
Cli 17
Lang 22
Closure 61
Math 41
Closure 52
Codec 2
Compress 30
Cli 5
JacksonDatabind 70
JacksonDatabind 16
Chart 20
Chart 4
Lang 40
JacksonDatabind 12
Codec 4
Mockito 34
Closure 86
Compress 31
Chart 17
Math 75
Chart 7
Csv 9
Closure 13
JacksonDatabind 27
Jsoup 88
Jsoup 45
Math 77
Math 79
Time 27
Math 30
Codec 16
Math 59
Closure 14
Gson 12
Jsoup 77
Jsoup 62
Cli 28
Math 50
Jsoup 6
JacksonDatabind 71
Gson 13
Closure 77
Jsoup 54
Compress 38
Compress 47"""

# Function to parse bugs into a dictionary
def parse_bugs(bug_list):
    parsed = {}
    for bug in bug_list:
        project = bug.split(" ")[0]
        if project not in parsed:
            parsed[project] = 0
        parsed[project] += 1
    return parsed

# Parse normalized datasets
chatrepair_data = parse_bugs(chatgpt_fixes.split("\n"))
iter_data = parse_bugs(iterlist.split("\n"))
selfapr_data = parse_bugs(self_apr.split("\n"))
repair_agent = parse_bugs(repair_agent_list.split("\n"))
# Define the total bugs for each project in defects4j
total_bugs = {
    "Chart": 26, "Cli": 39, "Closure": 174, "Codec": 18, "Collections": 4,
    "Compress": 47, "Csv": 16, "Gson": 18, "JacksonCore": 26, "JacksonDatabind": 112,
    "JacksonXml": 7, "Jsoup": 93, "JxPath": 22, "Lang": 63, "Math": 106,
    "Mockito": 38, "Time": 26
}

# number of plausible patches that went through manual analysis
plausibles = {
    "Chart": 14, "Cli": 9, "Closure": 27, "Codec": 10, "Collections": 1,
    "Compress": 10, "Csv": 6, "Gson": 3, "JacksonCore": 5, "JacksonDatabind": 18,
    "JacksonXml": 1, "Jsoup": 18, "JxPath": 0, "Lang": 17, "Math": 29,
    "Mockito": 6, "Time": 3
}

# Initialize table
table = PrettyTable()
table.field_names = ["Project", "Bugs", "Plausible", "Correct", "ChatRepair", "ITER", "SelfAPR"]

# Fill table rows
for project, bugs in total_bugs.items():
    plausible = plausibles.get(project, 0)
    correct = repair_agent.get(project, 0)
    chatrepair = chatrepair_data.get(project, 0)
    iter_fixes = iter_data.get(project, 0)
    selfapr = selfapr_data.get(project, 0)
    table.add_row([project, bugs, plausible, correct, chatrepair, iter_fixes, selfapr])

# Add summary row
total_row = [
    "Total",
    sum(total_bugs.values()),
    sum(plausibles.values()),
    sum(repair_agent.values()),  
    sum(chatrepair_data.values()),
    sum(iter_data.values()),
    sum(selfapr_data.values())
]
table.add_row(total_row)

# Print table
print(table)
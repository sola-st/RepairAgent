# 1. Identifying candidates (i.e., candidate locations) for a deleted statement
Generally, the candidates for a deleted statement are the previous executable statement and the next executable statement.


### 1.1 Methodology
We only consider the lexical structure of a program and the control flow graph (no slicing, no following of def-use chains). We require the next executable statement to be the closest executable statement that appears lexically after the deleted statement. We require the previous executable statement to be the closest executable statement that appears lexically before the deleted statement. The rationale is that a programmer is looking at the source code:  a tool should report lines that are as close as possible, in the source code, to the deleted statement.

Considering the control flow graph or the lexical structure of a program gives the same result for all non-conditional statements. We generally consider the control flow graph to determine the previous and next executable statements with the exception of loops. Within loops, we look only forward when determining the next executable statement:  If the last statement in a loop body is missing, the next executable statement appears after the loop body (i.e., we ignore the edge back to the condition of the loop). For consistency, the set of previous executable statements of a deleted statement that appears immediately after a for loop includes the last statement in the for loop body (see example in Section 1.2.3).

For a deleted statement that could be inserted in multiple locations, the set of candidate locations is the union of the next executable and previous executable statement(s) for each of those insertion locations.


##### Including non-executable statements
When looking for the previous or next executable statement, we include all of the following but continue:

* Declarations (including synchronized)
* Labels
* Curly braces (but see below for a case when we stop at a curly brace)

We stop at an executable statement.

##### Other rules
* The beginning of a declaration of a method, constructor, or static initializer is the **first** possible executable **statement** in that method, constructor, or initializer.
* The closing curly brace of a method, constructor, or static initializer is the **last** possible executable **statement** in that method, constructor, or initializer.
* We do **not** include empty lines and comments.


##### Multi-statement lines and multi-line statements
* Line breaks are irrelevant. We apply the same methodology for a single-statement line, a multi-statement line, or a multi-line statement.
* Example: `case x: foo(); break;`
    * If `foo()` is deleted:
        * To determine the previous executable statement, consider `case x:`, include it as a candidate because it is non-executable, and continue looking on the previous line. This would be the same if `case x:`, appeared on its own line above `foo()`. `break` is the next executable statement. 
    * If `break` is deleted:
        * `foo()` is the previous executable statement look for the next executable statement on the next line(s).


### 1.2 Examples
![CFGs](cfg.png)

In each of the following examples, the markers (<--) point to the previous and next executable statements.


#### 1.2.1 Deletion after If-else statement
Include both branches when the previous statement is a conditional statement---see nodes 2, 3, and 4 in CFG a):
```
1 if(x) {
2   foo();              <-- previous statement
3 } else {
4   bar();              <-- previous statement
5 } 
6 // deleted statement
7 nextStmt;             <-- next statement
```
**Candidates: 2, 3, 4, 5, 7**


#### 1.2.2 Deletion after If statement
Include both branches, one of which is missing so the CFG connects directly to the condition---see nodes 1, 2, and 3 in CFG b):
```
1 if(x) {               <-- previous statement
2   foo();              <-- previous statement
3 } 
4 // deleted statement
5 nextStmt;             <-- next statement
```
**Candidates: 1, 2, 3, 5**


#### 1.2.3 Deletion after a loop
Include both previous executable statements, lexically and according to the CFG---see nodes 1, 2, and 3 in CFG c):
```
1 for(x) {              <-- previous statement
2   foo();              <-- previous statement
3 } 
4 // deleted statement
5 nextStmt;             <-- next statement
```
**Candidates: 1, 2, 3, 5**


#### 1.2.4 Deletion at the end of a loop body
Include the lexically next executable statement---that is, skip node 1 in CFG c):
```
1 for(x) {
2   foo();              <-- previous statement
3 // deleted statement
4 } 
5 nextStmt;             <-- next statement
```
**Candidates: 2, 4, 5**


#### 1.2.5 Deletion at the end of a try block (within a try-catch-finally block)
Exclude the catch block:
```
1  try {
2    ...
3    if (x) {           <-- previous statement
4      // deleted statement   
5    }
6  } catch (y) {
7    ...
8  } finally {
9    nextStmt;          <-- next statement
10 }
```
**Candidates: 3, 5, 6, 8, 9**


#### 1.2.6 Deletion at the end of a try block (within a try-catch block)
Exclude the catch block:
```
1  try {
2    ...
3    if (x) {           <-- previous statement
4      // deleted statement   
5    }
6  } catch (y) {
7    ...
8  }
9  nextStmt;            <-- next statement
```
**Candidates: 3, 5, 6, 9**


#### 1.2.7 Deletion at the beginning of a method body
Include the declaration as the previous executable stmt:
```
1  public void foo () { <-- previous statement
2    // deleted statement   
3    nextStmt;          <-- next statement
4  }
```
**Candidates: 1, 3**


#### 1.2.8 Multiple candidate locations (e.g., deletion in an initializer block)
Include the previous and next executable statement(s) for each candidate locations: 
```
1 map = new HashMap();  <-- first possible previous statement
2 map.put(k1, v1);
3 // deleted statement   
4 map.put(k3, v3);
5 map.put(k4, v4);
6 return map;           <-- last possible next statement
```
**Candidates: 1-2, 4-6**

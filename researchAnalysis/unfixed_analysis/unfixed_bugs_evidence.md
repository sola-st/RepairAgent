# Unfixed Bugs — Per-Bug Evidence Document (66 bugs)

**Experiment:** E34 (Spec-Guided Repair)
**Total unfixed:** 66 of 98 bugs (67.3%)

Base paths:
- Specs: `repair_agent/experimental_setups/experiment_34/spec_logs/`
- Logs: `repair_agent/experimental_setups/experiment_34/logs/`
- Patches: `repair_agent/defects4j/framework/projects/{Project}/patches/{num}.src.patch`

---

## Distribution Summary

| Category | Count | Sub-Reasons |
|----------|-------|-------------|
| STUCK_LOOP | 41 | SEARCH_SPACE (14), DOMAIN_KNOWLEDGE (13), ADD_VS_DELETE_BIAS (6), STRATEGY_RIGID (5), SIMILARITY_BLOCKED_WRONG (3) |
| COMPILE_ERROR | 10 | ADD_VS_DELETE_BIAS (3), FORMAT_ERROR (3), MULTI_LINE_FORMAT (1), CLOSE_BUT_WRONG (1), SCOPE_OVERWHELM (1), OVERFITTING (1) |
| TEST_FAILURE | 6 | CLOSE_BUT_WRONG (2), ADD_VS_DELETE_BIAS (1), SCOPE_OVERWHELM (1), FORMAT_ERROR (1), OVERFITTING (1) |
| WRONG_DIRECTION | 5 | OVERFITTING (2), SCOPE_OVERWHELM (1), ANALYSIS_PARALYSIS (2) |
| TIMEOUT | 2 | ANALYSIS_PARALYSIS (2) |
| INFRA_BLOCKED | 2 | Tool similarity constraint rejected correct fix |

Spec helpfulness across all 66: **HELPFUL 20, NEUTRAL 17, MISLEADING 29** (44% misleading)

---

## INFRA_BLOCKED (2 bugs)

### Lang_52
| Field | Value |
|-------|-------|
| Sub-Reason | INFRA_BLOCKED (exact match fix rejected) |
| Spec | HELPFUL — correctly identified missing `case '/'` handler |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_52.json` |
| Agent Logs | `prompt_history_Lang_52/` |
| D4J Patch | `Lang/patches/52.src.patch` |
| Developer Fix | Add `case '/': out.write('\\'); out.write('/'); break;` before `default :` case |
| Agent Behavior | Produced identical fix but used `modifications` (70% similarity check) instead of `insertions`; 45% similarity caused rejection |

### Compress_24
| Field | Value |
|-------|-------|
| Sub-Reason | INFRA_BLOCKED (semantically equivalent fix rejected) |
| Spec | HELPFUL — identified premature IllegalArgumentException on valid tar headers |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_24.json` |
| Agent Logs | `prompt_history_Compress_24/` |
| D4J Patch | `Compress/patches/24.src.patch` |
| Developer Fix | Restructure while loop to if/else with single decrement + new while loop with `start < end - 1` |
| Agent Behavior | Attempted same restructure but 7 modified lines all had 20-47% similarity; multi-line structural changes inherently fail similarity check |

---

## STUCK_LOOP (41 bugs)

### Time_2
| Field | Value |
|-------|-------|
| Sub-Reason | SIMILARITY_BLOCKED_WRONG |
| Spec | HELPFUL — identified unsupported field ordering issue |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Time_2.json` |
| Agent Logs | `prompt_history_Time_2/` |
| D4J Patch | `Time/patches/2.src.patch` |
| Developer Fix | Fix unsupported field ordering in Partial by checking isSupported() flag and adjusting range duration field comparison |
| Agent Behavior | Struggled with complex field ordering constraints; missed that unsupported fields need special handling in range duration comparison |

### Time_4
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — misdirected on constructor parameter ordering |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Time_4.json` |
| Agent Logs | `prompt_history_Time_4/` |
| D4J Patch | `Time/patches/4.src.patch` |
| Developer Fix | Fix Partial.with() constructor call to pass chronology as first parameter via validated public constructor |
| Agent Behavior | Correctly identified constructor validation requirement but misunderstood parameter ordering for proper validation |

### Time_8
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | HELPFUL — identified missing sign combination validation |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Time_8.json` |
| Agent Logs | `prompt_history_Time_8/` |
| D4J Patch | `Time/patches/8.src.patch` |
| Developer Fix | Add validation to reject positive hoursOffset with negative minutesOffset; adjust minute offset calculation |
| Agent Behavior | Identified missing exception check but failed to properly integrate with minute offset calculation for negative hours |

### Time_10
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — overemphasized constant usage |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Time_10.json` |
| Agent Logs | `prompt_history_Time_10/` |
| D4J Patch | `Time/patches/10.src.patch` |
| Developer Fix | Remove unsafe constant and replace with 0L when setting partial fields; account for invalid dates like Feb 29 |
| Agent Behavior | Assumed constant was necessary; didn't recognize the invalid date edge case requiring direct 0L usage |

### Time_12
| Field | Value |
|-------|-------|
| Sub-Reason | STRATEGY_RIGID |
| Spec | HELPFUL — identified missing era handling for BC dates |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Time_12.json` |
| Agent Logs | `prompt_history_Time_12/` |
| D4J Patch | `Time/patches/12.src.patch` |
| Developer Fix | Handle BC date conversion by extracting era and adjusting year computation; remove broken BC year arithmetic |
| Agent Behavior | Recognized era handling was missing but applied incomplete fixes; didn't consistently remove broken BC conversion logic |

### Math_10
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | NEUTRAL — identified atan2 but didn't mention IEEE 754 signed-zero |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_10.json` |
| Agent Logs | `prompt_history_Math_10/` |
| D4J Patch | `Math/patches/10.src.patch` |
| Developer Fix | Use `Double.doubleToLongBits()` to distinguish +0.0 from -0.0; add 8 special-case combinations |
| Agent Behavior | 27 variations of `y == 0.0` checks; never discovered `Double.doubleToLongBits()` — the only way to distinguish signed zeros |

### Math_31
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | HELPFUL — identified numerical stability issue |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_31.json` |
| Agent Logs | `prompt_history_Math_31/` |
| D4J Patch | `Math/patches/31.src.patch` |
| Developer Fix | Rewrite continued fraction algorithm with proper scaling (Lentz modification) for infinity/overflow handling |
| Agent Behavior | Grasped numerical stability concept but couldn't synthesize the complex dual-variable scaling loop |

### Math_44
| Field | Value |
|-------|-------|
| Sub-Reason | STRATEGY_RIGID |
| Spec | NEUTRAL — identified flag reset issue |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_44.json` |
| Agent Logs | `prompt_history_Math_44/` |
| D4J Patch | `Math/patches/44.src.patch` |
| Developer Fix | Remove premature resetOccurred=false flag and delete spurious stepAccepted calls |
| Agent Behavior | Identified flag reset issue but incorrectly added deletion logic for stepAccepted calls required in other contexts |

### Math_47
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | HELPFUL — mentioned preconditioning from code comments |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_47.json` |
| Agent Logs | `prompt_history_Math_47/` |
| D4J Patch | `Math/patches/47.src.patch` |
| Developer Fix | Implement cross-product preconditioning by computing scale factors and preconditioned vector v3 |
| Agent Behavior | Understood preconditioning concept but lacked mathematical precision to derive v3 computation formula |

### Math_55
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — suggested isZero flag was reliable |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_55.json` |
| Agent Logs | `prompt_history_Math_55/` |
| D4J Patch | `Math/patches/55.src.patch` |
| Developer Fix | Reconstruct Complex.divide() special case with direct component comparison instead of cached isZero flag |
| Agent Behavior | Found divisor check but spec misleadingly pointed to isZero flag; patches didn't restore proper zero-detection |

### Math_78
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | NEUTRAL — identified bracketing issue |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_78.json` |
| Agent Logs | `prompt_history_Math_78/` |
| D4J Patch | `Math/patches/78.src.patch` |
| Developer Fix | Add corner-case sign-change detection with epsilon-based ta adjustment loop for Brent solver bracketing |
| Agent Behavior | Attempted bracketing logic but created infinite adjustment loops; missed limited iteration count constraint |

### Math_81
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — vague about OR vs AND condition relationship |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_81.json` |
| Agent Logs | `prompt_history_Math_81/` |
| D4J Patch | `Math/patches/81.src.patch` |
| Developer Fix | Correct loop range from 4*n0-16 to 4*n0-11 and change OR to AND in eigenvalue convergence tests |
| Agent Behavior | Found loop bound issues but couldn't determine correct relationship between condition logic and numerical correctness |

### Math_88
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — suggested multiple approaches without clarifying correct one |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_88.json` |
| Agent Logs | `prompt_history_Math_88/` |
| D4J Patch | `Math/patches/88.src.patch` |
| Developer Fix | Simplify solution extraction by removing basicRows HashSet and implementing basic row conflict detection via tableau column inspection |
| Agent Behavior | Struggled with whether to add/delete HashSet or refactor; couldn't determine correct conflict resolution strategy |

### Math_92
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | HELPFUL — identified precision issues with Math.round |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_92.json` |
| Agent Logs | `prompt_history_Math_92/` |
| D4J Patch | `Math/patches/92.src.patch` |
| Developer Fix | Replace piecewise binomial coefficient with log-space evaluation using binomialCoefficientLog and Math.floor |
| Agent Behavior | Correctly identified precision issues but couldn't synthesize the logarithmic reformulation for large n values |

### Math_93
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — indicated rounding errors but not the algorithmic simplification needed |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Math_93.json` |
| Agent Logs | `prompt_history_Math_93/` |
| D4J Patch | `Math/patches/93.src.patch` |
| Developer Fix | Remove overflow check and precision-based fallback; delegate to `Math.round(factorialDouble(n))` |
| Agent Behavior | Stuck in understanding precision requirements; couldn't refactor to simpler algorithm |

### Lang_1
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — overspecified hex digit checks when fix is operator-only |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_1.json` |
| Agent Logs | `prompt_history_Lang_1/` |
| D4J Patch | `Lang/patches/1.src.patch` |
| Developer Fix | Change threshold from `hexDigits > 16` to compound condition checking count AND leading digit |
| Agent Behavior | 35 variants cycling through `>= 16`, `> 16`, `== 16`; never synthesized compound condition with two variables |

### Lang_3
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — indicated missing code when fix requires deletion |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_3.json` |
| Agent Logs | `prompt_history_Lang_3/` |
| D4J Patch | `Lang/patches/3.src.patch` |
| Developer Fix | Remove numDecimal filters blocking Float/Double attempts; always try before falling back |
| Agent Behavior | Assumed spec indicated missing code; actually requires deletion of guard conditions |

### Lang_5
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — suggested missing locale parsing |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_5.json` |
| Agent Logs | `prompt_history_Lang_5/` |
| D4J Patch | `Lang/patches/5.src.patch` |
| Developer Fix | Remove entire underscore-prefix handling block (lines 97-127) |
| Agent Behavior | Spec points to missing locale parsing; actual fix is complete code removal for underscore cases |

### Lang_12
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — flagged empty array check as violation but fix removes it |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_12.json` |
| Agent Logs | `prompt_history_Lang_12/` |
| D4J Patch | `Lang/patches/12.src.patch` |
| Developer Fix | Remove empty array validation and chars array default assignment; simplify start/end init logic |
| Agent Behavior | Couldn't reconcile spec's violation flag with the need to delete the flagged code entirely |

### Lang_30
| Field | Value |
|-------|-------|
| Sub-Reason | SIMILARITY_BLOCKED_WRONG |
| Spec | NEUTRAL — highlighted feature missing but fix removes it |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_30.json` |
| Agent Logs | `prompt_history_Lang_30/` |
| D4J Patch | `Lang/patches/30.src.patch` |
| Developer Fix | Remove surrogate pair handling logic from containsAny; simplify to ignore supplementary chars |
| Agent Behavior | Surrogate pair detection is premature/wrong; spec highlights feature gap but fix removes the feature entirely |

### Lang_32
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — emphasized registry not cleared when fix is ThreadLocal pattern refactoring |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_32.json` |
| Agent Logs | `prompt_history_Lang_32/` |
| D4J Patch | `Lang/patches/32.src.patch` |
| Developer Fix | Change ThreadLocal initialization to anonymous class with initialValue(); remove manual null checks |
| Agent Behavior | Focused on registry clearing rather than recognizing ThreadLocal pattern was fundamentally wrong |

### Lang_36
| Field | Value |
|-------|-------|
| Sub-Reason | STRATEGY_RIGID |
| Spec | MISLEADING — detailed array notation as violation when fix removes entire feature |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_36.json` |
| Agent Logs | `prompt_history_Lang_36/` |
| D4J Patch | `Lang/patches/36.src.patch` |
| Developer Fix | Remove all array encoding logic (prefix tracking, L/; stripping); return unmodified inner class output |
| Agent Behavior | Tried to fix array notation handling; never considered removing the feature entirely |

### Lang_41
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — correctly said "/" shouldn't be escaped but agent couldn't remove parameter-based control flow |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_41.json` |
| Agent Logs | `prompt_history_Lang_41/` |
| D4J Patch | `Lang/patches/41.src.patch` |
| Developer Fix | Remove forward slash escaping from escapeJavaStyleString; remove escapeForwardSlash parameter |
| Agent Behavior | Understood the issue but couldn't remove parameter-based control flow across method signatures |

### Lang_46
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — indicated "/" should not be escaped; fix requires deletion of two conditional arms |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_46.json` |
| Agent Logs | `prompt_history_Lang_46/` |
| D4J Patch | `Lang/patches/46.src.patch` |
| Developer Fix | Remove both forward slash escape cases from JavaScript writer |
| Agent Behavior | Tried to add alternative handling rather than simply deleting the escape cases |

### Lang_50
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — flagged !Character.isDigit(lastChar) but fix removes '.' from condition |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_50.json` |
| Agent Logs | `prompt_history_Lang_50/` |
| D4J Patch | `Lang/patches/50.src.patch` |
| Developer Fix | Remove decimal point from lastChar validation; allow trailing period in number formats |
| Agent Behavior | Focused on digit checking rather than recognizing the '.' exclusion was the actual bug |

### Lang_53
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | HELPFUL — clearly described locale variant parsing rule |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_53.json` |
| Agent Logs | `prompt_history_Lang_53/` |
| D4J Patch | `Lang/patches/53.src.patch` |
| Developer Fix | Remove '3' character check for variant parsing; allow 'fr__POSIX' variant without country |
| Agent Behavior | Understood rule from spec but couldn't override strict parsing rules in implementation |

### Lang_54
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | HELPFUL — correctly identified underscore variant issue |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_54.json` |
| Agent Logs | `prompt_history_Lang_54/` |
| D4J Patch | `Lang/patches/54.src.patch` |
| Developer Fix | Remove variant parsing logic for underscore prefix; simplify underscore handling |
| Agent Behavior | Correctly identified issue but stuck on code structure complexity |

### Lang_64
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — emphasized adding checks when fix removes complex logic |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Lang_64.json` |
| Agent Logs | `prompt_history_Lang_64/` |
| D4J Patch | `Lang/patches/64.src.patch` |
| Developer Fix | Remove overly complex cross-classloader enum comparison; leave only simple iValue subtraction |
| Agent Behavior | Tried to ADD null/type checks when fix required REMOVING complex comparison logic |

### Compress_11
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — said exception handling was missing; actual fix removes a guard condition |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_11.json` |
| Agent Logs | `prompt_history_Compress_11/` |
| D4J Patch | `Compress/patches/11.src.patch` |
| Developer Fix | Remove conditional guard `if (signatureLength >= 512)` that prevented TAR detection |
| Agent Behavior | Searched for code to throw ArchiveException when fix was removing a premature guard |

### Compress_17
| Field | Value |
|-------|-------|
| Sub-Reason | STRATEGY_RIGID |
| Spec | NEUTRAL — accurately described problem |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_17.json` |
| Agent Logs | `prompt_history_Compress_17/` |
| D4J Patch | `Compress/patches/17.src.patch` |
| Developer Fix | Change while loop checking multiple trailing NULs/spaces to single if statement |
| Agent Behavior | Tried to fix loop conditions; never considered simplifying while to if |

### Compress_35
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — said code was missing; fix replaces parseOctal() with manual parsing |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_35.json` |
| Agent Logs | `prompt_history_Compress_35/` |
| D4J Patch | `Compress/patches/35.src.patch` |
| Developer Fix | Replace parseOctal() call with manual octal parsing loop extracting 6-digit checksum |
| Agent Behavior | Added missing exception handling when fix required refactoring the extraction method |

### Compress_36
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | HELPFUL — correctly identified overflow handling as problematic |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_36.json` |
| Agent Logs | `prompt_history_Compress_36/` |
| D4J Patch | `Compress/patches/36.src.patch` |
| Developer Fix | Remove special overflow handling for bitsCachedSize >= 57; simplify by allowing arbitrary bit caching |
| Agent Behavior | Over-engineered fixes; simple deletion of overflow logic was needed |

### Compress_40
| Field | Value |
|-------|-------|
| Sub-Reason | STRATEGY_RIGID |
| Spec | NEUTRAL — indicated missing check |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_40.json` |
| Agent Logs | `prompt_history_Compress_40/` |
| D4J Patch | `Compress/patches/40.src.patch` (note: may share with 45) |
| Developer Fix | Remove else block containing formatBigIntegerBinary(); call unconditionally |
| Agent Behavior | Strategy of adding missing code didn't match the unintuitive control flow change needed |

### Compress_45
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — emphasized missing parser state checks; fix is structural refactoring |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Compress_45.json` |
| Agent Logs | `prompt_history_Compress_45/` |
| D4J Patch | `Compress/patches/45.src.patch` |
| Developer Fix | Remove csvRecordIterator field; move iterator to anonymous class inside iterator() method |
| Agent Behavior | Tried to add state checks rather than refactor field into local anonymous class |

### Csv_16
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | MISLEADING — emphasized missing parser state logic; fix removes a field and refactors |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Csv_16.json` |
| Agent Logs | `prompt_history_Csv_16/` |
| D4J Patch | `Csv/patches/16.src.patch` |
| Developer Fix | Remove csvRecordIterator field and initialization; convert iterator() to return anonymous inner class |
| Agent Behavior | ADD bias led agent away from deletion+refactoring strategy |

### Codec_11
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — listed line-specific violations for a massive refactoring fix |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Codec_11.json` |
| Agent Logs | `prompt_history_Codec_11/` |
| D4J Patch | `Codec/patches/11.src.patch` |
| Developer Fix | Remove 6 helper methods, change return type, simplify encoding loop, change decoder CRLF handling |
| Agent Behavior | Trapped in local fixes when fix required massive multi-method refactoring |

### Codec_13
| Field | Value |
|-------|-------|
| Sub-Reason | DOMAIN_KNOWLEDGE |
| Spec | MISLEADING — mentioned null handling; fix deletes entire utility class |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Codec_13.json` |
| Agent Logs | `prompt_history_Codec_13/` |
| D4J Patch | `Codec/patches/13.src.patch` |
| Developer Fix | Delete CharSequenceUtils.java entirely; remove StringUtils.equals(); use String.equals() directly |
| Agent Behavior | Tried to add null checks; never recognized need for API-level change (deleting utility class) |

### Collections_2
| Field | Value |
|-------|-------|
| Sub-Reason | SIMILARITY_BLOCKED_WRONG |
| Spec | HELPFUL — correctly identified method was backwards (retainAll vs removeAll) |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Collections_2.json` |
| Agent Logs | `prompt_history_Collections_2/` |
| D4J Patch | `Collections/patches/2.src.patch` |
| Developer Fix | Change `ListUtils.retainAll()` to `ListUtils.removeAll()` — single method name fix |
| Agent Behavior | Tried complex conditional logic rather than recognizing simple method name inversion |

### Collections_3
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — emphasized initialization/instance variable logic |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Collections_3.json` |
| Agent Logs | `prompt_history_Collections_3/` |
| D4J Patch | `Collections/patches/3.src.patch` |
| Developer Fix | Remove instance variable includePropertyName; revert to static field; replace while loop with if check |
| Agent Behavior | Trapped in scope/initialization fixes; couldn't see need to remove instance variable entirely |

### Collections_7
| Field | Value |
|-------|-------|
| Sub-Reason | SEARCH_SPACE |
| Spec | MISLEADING — focused on individual method issues |
| Attempts | 40 |
| Spec File | `spec_parsed_json_Collections_7.json` |
| Agent Logs | `prompt_history_Collections_7/` |
| D4J Patch | `Collections/patches/7.src.patch` |
| Developer Fix | Delete put()/remove() overrides from ExtendedProperties (15+ lines); change super calls to this calls |
| Agent Behavior | Tried to fix individual method implementations; didn't see inheritance pattern requiring override removal |

---

## COMPILE_ERROR (10 bugs)

### Time_3
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | HELPFUL — identified guard removal needed |
| Attempts | 36 |
| Spec File | `spec_parsed_json_Time_3.json` |
| Agent Logs | `prompt_history_Time_3/` |
| D4J Patch | `Time/patches/3.src.patch` |
| Developer Fix | Remove unnecessary null-check guards wrapping setMillis() calls in add methods (2 line deletions per method) |
| Agent Behavior | Attempted complex DST handling instead of simple guard removal |

### Time_5
| Field | Value |
|-------|-------|
| Sub-Reason | SCOPE_OVERWHELM |
| Spec | HELPFUL — showed simpler modulo-based approach |
| Attempts | 36 |
| Spec File | `spec_parsed_json_Time_5.json` |
| Agent Logs | `prompt_history_Time_5/` |
| D4J Patch | `Time/patches/5.src.patch` |
| Developer Fix | Simplify Period.normalizedStandard() by removing field-support checks and using modular arithmetic |
| Agent Behavior | Got trapped trying conditional checks when simpler modulo approach was needed |

### Math_106
| Field | Value |
|-------|-------|
| Sub-Reason | FORMAT_ERROR |
| Spec | HELPFUL — identified validation removal needed |
| Attempts | 12 |
| Spec File | `spec_parsed_json_Math_106.json` |
| Agent Logs | `prompt_history_Math_106/` |
| D4J Patch | `Math/patches/106.src.patch` |
| Developer Fix | Remove minus-sign validation checks for numerator and denominator in ProperFractionFormat.parse() |
| Agent Behavior | Understood problem but struggled formatting removal of 4 duplicate validation blocks |

### Lang_17
| Field | Value |
|-------|-------|
| Sub-Reason | MULTI_LINE_FORMAT |
| Spec | HELPFUL — identified surrogate pair and consumed/else logic |
| Attempts | 34 |
| Spec File | `spec_parsed_json_Lang_17.json` |
| Agent Logs | `prompt_history_Lang_17/` |
| D4J Patch | `Lang/patches/17.src.patch` |
| Developer Fix | Refactor CharSequenceTranslator.translate() to use codePointCount; restructure consumed/else branching (15+ lines) |
| Agent Behavior | Struggled with complex surrogate pair handling across 15+ interdependent lines |

### Lang_31
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | HELPFUL — identified surrogate pair removal |
| Attempts | 14 |
| Spec File | `spec_parsed_json_Lang_31.json` |
| Agent Logs | `prompt_history_Lang_31/` |
| D4J Patch | `Lang/patches/31.src.patch` |
| Developer Fix | Remove surrogate pair check and nested conditional in StringUtils.containsAny(); simplify to single-char matching |
| Agent Behavior | Wanted to add supplementary character logic when deletion of existing branch was needed |

### Codec_6
| Field | Value |
|-------|-------|
| Sub-Reason | FORMAT_ERROR |
| Spec | NEUTRAL — didn't clarify loop structure |
| Attempts | 11 |
| Spec File | `spec_parsed_json_Codec_6.json` |
| Agent Logs | `prompt_history_Codec_6/` |
| D4J Patch | `Codec/patches/6.src.patch` |
| Developer Fix | Remove readLen variable and while-loop wrapper in Base64InputStream.read(); return directly |
| Agent Behavior | Confused about control flow simplification necessity |

### Codec_15
| Field | Value |
|-------|-------|
| Sub-Reason | CLOSE_BUT_WRONG |
| Spec | MISLEADING — original loop direction was wrong |
| Attempts | 33 |
| Spec File | `spec_parsed_json_Codec_15.json` |
| Agent Logs | `prompt_history_Codec_15/` |
| D4J Patch | `Codec/patches/15.src.patch` |
| Developer Fix | Restructure HW-rule logic in Soundex.getMappingCode() from backward loop to forward peek-ahead |
| Agent Behavior | Attempted variant loops instead of structural inversion of the iteration direction |

### Collections_17
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | NEUTRAL — didn't clarify instantiation pattern |
| Attempts | 32 |
| Spec File | `spec_parsed_json_Collections_17.json` |
| Agent Logs | `prompt_history_Collections_17/` |
| D4J Patch | `Collections/patches/17.src.patch` |
| Developer Fix | Change EqualPredicate constructor to instantiate DefaultEquator instead of passing null |
| Agent Behavior | Wanted to add null-check logic instead of changing instantiation |

### Collections_25
| Field | Value |
|-------|-------|
| Sub-Reason | OVERFITTING |
| Spec | NEUTRAL — didn't clarify null-handling removal |
| Attempts | 34 |
| Spec File | `spec_parsed_json_Collections_25.json` |
| Agent Logs | `prompt_history_Collections_25/` |
| D4J Patch | `Collections/patches/25.src.patch` |
| Developer Fix | Remove null-check and NATURAL_COMPARATOR fallback in collatedIterator(); pass comparator directly |
| Agent Behavior | Over-fit to defensive programming patterns instead of simplifying |

### Compress_29
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | HELPFUL — identified encoding issues |
| Attempts | 34 |
| Spec File | `spec_parsed_json_Compress_29.json` |
| Agent Logs | `prompt_history_Compress_29/` |
| D4J Patch | `Compress/patches/29.src.patch` |
| Developer Fix | Remove entryEncoding conditional branches and unused encoding fields from multiple stream classes |
| Agent Behavior | Tried adding encoding support instead of removing it; wanted to expand conditionals |

---

## TEST_FAILURE (6 bugs)

### Math_9
| Field | Value |
|-------|-------|
| Sub-Reason | CLOSE_BUT_WRONG |
| Spec | MISLEADING — suggested revert was wrong type of transformation |
| Attempts | 26 |
| Spec File | `spec_parsed_json_Math_9.json` |
| Agent Logs | `prompt_history_Math_9/` |
| D4J Patch | `Math/patches/9.src.patch` |
| Developer Fix | Revert Line constructor body from copy-then-modify to direct initialization with zero subtracted from direction |
| Agent Behavior | Attempted multiple setter approaches instead of direct initialization pattern |

### Lang_65
| Field | Value |
|-------|-------|
| Sub-Reason | SCOPE_OVERWHELM |
| Spec | MISLEADING — 8 locations marked "CODE IS MISSING" when fix is 25-line deletion |
| Attempts | 22 |
| Spec File | `spec_parsed_json_Lang_65.json` |
| Agent Logs | `prompt_history_Lang_65/` |
| D4J Patch | `Lang/patches/65.src.patch` |
| Developer Fix | Delete entire 25-line LANG-59 section of raw millisecond arithmetic that bypasses Calendar timezone handling |
| Agent Behavior | 21 attempts adding truncation code at empty comment lines; never considered deleting the LANG-59 section |

### Collections_5
| Field | Value |
|-------|-------|
| Sub-Reason | OVERFITTING |
| Spec | MISLEADING — showed indexed insertion as necessary |
| Attempts | 25 |
| Spec File | `spec_parsed_json_Collections_5.json` |
| Agent Logs | `prompt_history_Collections_5/` |
| D4J Patch | `Collections/patches/5.src.patch` |
| Developer Fix | Simplify SetUniqueList.addAll() by removing index-tracking and size-checking; use unindexed add() |
| Agent Behavior | Over-fit to tracking index changes when simpler unindexed approach was correct |

### Collections_8
| Field | Value |
|-------|-------|
| Sub-Reason | FORMAT_ERROR |
| Spec | NEUTRAL — didn't clarify serialization strategy |
| Attempts | 32 |
| Spec File | `spec_parsed_json_Collections_8.json` |
| Agent Logs | `prompt_history_Collections_8/` |
| D4J Patch | `Collections/patches/8.src.patch` |
| Developer Fix | Refactor UnboundedFifoBuffer serialization to write size only (not buffer length); read size then allocate size+1 |
| Agent Behavior | Unable to bridge write/read protocol mismatch across two interdependent methods |

### Collections_15
| Field | Value |
|-------|-------|
| Sub-Reason | CLOSE_BUT_WRONG |
| Spec | MISLEADING — showed condition inversion needed but agent got deletion order wrong |
| Attempts | 35 |
| Spec File | `spec_parsed_json_Collections_15.json` |
| Agent Logs | `prompt_history_Collections_15/` |
| D4J Patch | `Collections/patches/15.src.patch` |
| Developer Fix | Invert set() condition: if pos == -1 OR pos == index, return; else remove duplicate then remove old |
| Agent Behavior | Attempted variations of deletion order but couldn't nail the exact condition inversion |

### Compress_4
| Field | Value |
|-------|-------|
| Sub-Reason | ADD_VS_DELETE_BIAS |
| Spec | HELPFUL — identified finish() call distribution issue |
| Attempts | 28 |
| Spec File | `spec_parsed_json_Compress_4.json` |
| Agent Logs | `prompt_history_Compress_4/` |
| D4J Patch | `Compress/patches/4.src.patch` |
| Developer Fix | Add finish() calls to close() methods in multiple archive output streams; remove from ChangeSetPerformer |
| Agent Behavior | Wanted to consolidate finish() rather than distribute calls across subclasses |

---

## WRONG_DIRECTION (5 bugs)

### Math_13
| Field | Value |
|-------|-------|
| Sub-Reason | ANALYSIS_PARALYSIS |
| Spec | NEUTRAL — didn't clarify algorithm choice |
| Attempts | 17 |
| Spec File | `spec_parsed_json_Math_13.json` |
| Agent Logs | `prompt_history_Math_13/` |
| D4J Patch | `Math/patches/13.src.patch` |
| Developer Fix | Delete entire DiagonalMatrix-specific optimization branch in squareRoot(); always use EigenDecomposition |
| Agent Behavior | Unable to decide between optimization paths; kept trying to fix DiagonalMatrix branch |

### Math_36
| Field | Value |
|-------|-------|
| Sub-Reason | OVERFITTING |
| Spec | HELPFUL — identified NaN overflow issue but not the bit-shift algorithm |
| Attempts | 32 |
| Spec File | `spec_parsed_json_Math_36.json` |
| Agent Logs | `prompt_history_Math_36/` |
| D4J Patch | `Math/patches/36.src.patch` |
| Developer Fix | Add bit-shift scaling: when NaN, shift both numerator/denominator right by same amount to preserve ratio |
| Agent Behavior | Read `assertEquals(5, ...)` and hardcoded `return 5.0`; never attempted mathematical scaling |

### Math_66
| Field | Value |
|-------|-------|
| Sub-Reason | SCOPE_OVERWHELM |
| Spec | HELPFUL — showed API redesign needed |
| Attempts | 33 |
| Spec File | `spec_parsed_json_Math_66.json` |
| Agent Logs | `prompt_history_Math_66/` |
| D4J Patch | `Math/patches/66.src.patch` |
| Developer Fix | Major refactor of BrentOptimizer: constructor, optimize methods, add loop counter, remove state flags |
| Agent Behavior | Paralyzed by 33 interrelated changes across methods |

### Lang_7
| Field | Value |
|-------|-------|
| Sub-Reason | OVERFITTING |
| Spec | HELPFUL — identified double-negative prefix issue |
| Attempts | 28 |
| Spec File | `spec_parsed_json_Lang_7.json` |
| Agent Logs | `prompt_history_Lang_7/` |
| D4J Patch | `Lang/patches/7.src.patch` |
| Developer Fix | Add "--" prefix check returning null in createNumber(); remove "--" throw in createBigDecimal() |
| Agent Behavior | Over-fit to BigDecimal exception pattern when simpler null-return was needed |

### Compress_33
| Field | Value |
|-------|-------|
| Sub-Reason | ANALYSIS_PARALYSIS |
| Spec | MISLEADING — suggested deflate detection was wrong approach |
| Attempts | 36 |
| Spec File | `spec_parsed_json_Compress_33.json` |
| Agent Logs | `prompt_history_Compress_33/` |
| D4J Patch | `Compress/patches/33.src.patch` |
| Developer Fix | Delete DeflateCompressorInputStream.matches() method and remove its invocation in factory |
| Agent Behavior | Cycled through 36 detection implementations instead of recognizing the method should be deleted |

---

## TIMEOUT (2 bugs)

### Lang_23
| Field | Value |
|-------|-------|
| Sub-Reason | ANALYSIS_PARALYSIS |
| Spec | NEUTRAL — correctly identified equals/hashCode issue but "CODE IS MISSING" language misled |
| Attempts | 0 (zero fix attempts; 28 extract_method_code calls, 39 total turns) |
| Spec File | `spec_parsed_json_Lang_23.json` |
| Agent Logs | `prompt_history_Lang_23/` |
| D4J Patch | `Lang/patches/23.src.patch` |
| Developer Fix | Delete equals() and hashCode() overrides from ExtendedMessageFormat (~25 lines); remove HASH_SEED |
| Agent Behavior | 93% of budget on extract_method_code searching OTHER classes; never read the actual buggy file; 0 fix attempts |

### Compress_43
| Field | Value |
|-------|-------|
| Sub-Reason | ANALYSIS_PARALYSIS |
| Spec | NEUTRAL — indicated parameter design issue |
| Attempts | 4 |
| Spec File | `spec_parsed_json_Compress_43.json` |
| Agent Logs | `prompt_history_Compress_43/` |
| D4J Patch | `Compress/patches/43.src.patch` |
| Developer Fix | Simplify usesDataDescriptor() by removing phased parameter; update all call sites |
| Agent Behavior | Timeout hit due to parameter coordination complexity across multiple call sites |

---

## Cross-Cutting Analysis

### Sub-Reason Distribution (all 66 bugs)

| Sub-Reason | Count | % | Description |
|-----------|-------|---|-------------|
| SEARCH_SPACE | 14 | 21.2% | Fix requires compound/multi-variable/structural changes beyond agent's exploration |
| DOMAIN_KNOWLEDGE | 13 | 19.7% | Agent lacks specific technical knowledge (IEEE 754, Calendar DST, etc.) |
| ADD_VS_DELETE_BIAS | 12 | 18.2% | Agent adds code when developer fix removes/simplifies code |
| STRATEGY_RIGID | 5 | 7.6% | Agent repeats same approach without fundamental strategy change |
| ANALYSIS_PARALYSIS | 5 | 7.6% | Agent over-analyzes or can't decide; uses all turns reading |
| CLOSE_BUT_WRONG | 4 | 6.1% | Agent was near correct fix but couldn't nail exact logic |
| FORMAT_ERROR | 4 | 6.1% | Multi-line Java doesn't fit tool's single-line format |
| OVERFITTING | 4 | 6.1% | Agent hardcodes test values or over-fits to defensive patterns |
| SIMILARITY_BLOCKED_WRONG | 3 | 4.5% | Similarity check blocked fix AND fix direction was also wrong |
| SCOPE_OVERWHELM | 3 | 4.5% | Fix spans multiple files/methods beyond agent's coordination ability |
| MULTI_LINE_FORMAT | 1 | 1.5% | Complex multi-line structural change |
| INFRA_BLOCKED | 2 | 3.0% | Correct fix rejected by tool constraint |

### Spec Helpfulness (all 66 bugs)

| Rating | Count | % |
|--------|-------|---|
| HELPFUL | 20 | 30.3% |
| NEUTRAL | 17 | 25.8% |
| MISLEADING | 29 | 43.9% |

**Key insight:** 44% of specs were MISLEADING — primarily because they flagged "CODE IS MISSING" when the developer fix was to DELETE code. The spec generator's FAULT_OF_OMISSION annotation systematically misled the agent for deletion-type fixes.

### Developer Fix Patterns vs Agent Behavior

| Developer Fix Type | Count (est.) | Agent Default Behavior | Mismatch? |
|-------------------|-------------|----------------------|-----------|
| Delete/simplify code | ~30 | Add code | YES |
| Modify existing logic | ~20 | Modify (but wrong logic) | Partial |
| Add missing code | ~10 | Add code | No |
| Structural refactor | ~6 | Local line edits | YES |

**The fundamental mismatch:** ~45% of developer fixes involve deleting or simplifying code, but the agent's default behavior is to ADD code. Specs that say "CODE IS MISSING" reinforce this bias.

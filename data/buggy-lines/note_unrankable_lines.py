
import random
random.seed(0)

from pathlib import Path

PROJECTS = ['Chart', 'Cli', 'Closure', 'Codec', 'Collections', 'Compress', 'Csv', 'Gson', 'JacksonCore', 'JacksonDatabind', 'JacksonXml', 'Jsoup', 'JxPath', 'Lang', 'Math', 'Mockito', 'Time']
N_BUGS = {'Chart':26, 'Cli':40, 'Closure':176, 'Codec':18, 'Collections':28, 'Compress':47, 'Csv':16, 'Gson':18, 'JacksonCore':26, 'JacksonDatabind':112, 'JacksonXml':6, 'Jsoup':93, 'JxPath':22, 'Lang':65, 'Math':106, 'Mockito':38, 'Time':27}

def parse_buggy_line(buggy_line_info):
  path, lno, source = buggy_line_info.split(b'#', 2)
  return (path+b'#'+lno, source)

for project in PROJECTS:
  for bug in range(1, N_BUGS[project]+1):
    if Path('{}-{}.buggy.lines'.format(project, bug)).is_file() == False:
      # Some bugs on D4J 2.0 have been considered deprecated and for those there is no .buggy.lines file
      continue

    with open('{}-{}.buggy.lines'.format(project, bug), 'rb') as f:
      buggy_lines_needing_candidates = dict(parse_buggy_line(l.strip()) for l in f if b'FAULT_OF_OMISSION' in l or b'MISSING_RANKING_STATEMENT' in l)
    try:
      with open('{}-{}.candidates'.format(project, bug), 'rb') as f:
        buggy_lines_with_candidates = set(l.strip().split(b',')[0] for l in f)
    except IOError:
      buggy_lines_with_candidates = set()

    buggy_lines_needing_but_lacking_candidates = set(buggy_lines_needing_candidates.keys()) - buggy_lines_with_candidates

    if buggy_lines_needing_but_lacking_candidates:
      with open('{}-{}.unrankable.lines'.format(project, bug), 'wb') as f:
        f.write(b''.join(line+b'#'+buggy_lines_needing_candidates[line]+b'\n' for line in buggy_lines_needing_but_lacking_candidates))

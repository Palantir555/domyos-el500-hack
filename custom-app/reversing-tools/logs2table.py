# receives a log file with the following line format:
# "<meta> <direction>:  *<cmd>[<characteristic>][<value>]"
# direction is either "App to Target" or "Target to App"
# If meta is "ERROR", the line is ignored
# if the line does not match the regex, it is ignored but a warning is printed

import sys
import re
import csv

# regex to match the log lines
# the regex is split into 4 parts:
# 1. meta: the meta information
# 2. direction: the direction of the command
# 3. cmd: the command
# 4. characteristic: the characteristic
# 5. value: the value

parsed_msgs = set()
with open(sys.argv[1], 'r') as f:
    for line in f:
        if line.startswith("ERROR"):
            continue
        m = re.match(r'([^ ]*) (.*):[ ]*(.*)\[([^\]]*)\]\[([^\]]*)\]', line)
        if m is None:
            print("WARNING: line does not match regex: " + line)
            continue
        print(m.groups())
        parsed_msgs.add(m.groups())

# save parsed_msgs into a TSV file
with open(sys.argv[2], 'w') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(parsed_msgs)

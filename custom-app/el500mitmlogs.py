import re

# logs from the MITM attack, in this format: <Write|Notify>\t<hex data>
# Where hex data is an array of bytes separated by spaces
# TODO FIX UP THIS MESS
# mitm_clean_logfile = "mitm_clean.log"
mitm_dirty_logfile = "logsmitm-03-24_dirty.txt"
mitm_new_logfile = "mitm_new.tsv"

def cleanup_mitm_logfile():
    # This function removes all lines where "App to Target" uses "Notify", removes columns 0, 1 and 3. If a command (last column) does not start with "f0", it is appended to the previous line's command
    # Sample line ("App to Target" or "Target to App" are a single column):
    # <INFO> <App to Target>:  <Write>[<49535343-8841-43f4-a8d4-ecbe34729bb3>][<f0 a3 93>]
    def logs2table(loglines):
        parsed_msgs = []
        for line in loglines:
            if line.startswith("ERROR"):
                continue
            m = re.match(r'([^ ]*) (.*):[ ]*(.*)\[([^\]]*)\]\[([^\]]*)\]', line)
            if m is None:
                print("WARNING: line does not match regex: " + line)
                continue
            if m.group(2) == "App to Target" and m.group(3) == "Notify":
                continue # app only writes, it does not notify
            yield m.groups()

    with open(mitm_new_logfile, "w") as f:
        with open(mitm_dirty_logfile, "r") as g:
            for l in logs2table(g.readlines()):
                # Write a line in the format <Write|Notify>\t<hex data>
                # If l[4] does not start with ff, append it to the previous line's hex data
                if l[4].startswith("f0"):
                    f.write(f"\n{l[2]}\t{l[4]}")
                else:
                    f.write(f" {l[4]}") # append this message to the previous one
                    
                
            

def parse_tsvconversation(tsvdata):
    lines = tsvdata.split("\n")
    pairs = []
    for line in lines:
        if line.startswith("Write"):
            command = bytearray.fromhex(line.split("\t")[1])
            pairs.append((command, None))
        elif line.startswith("Notify"):
            response = bytearray.fromhex(line.split("\t")[1])
            pairs[-1] = (pairs[-1][0], response)

    for cmd, resp in pairs:
        if None in [cmd, resp]:
            continue
        # Make sure the command starts with f0
        assert (
            cmd[0] == 0xF0 and resp[0] == 0xF0
        ), f"Command or response doesn't start with f0: {cmd} {resp}"
        assert (
            cmd[1] & 0x0F == resp[1] & 0x0F
        ), "command and response second half of second byte do not match"
        assert (
            cmd[1] & 0xF0 == resp[1] & 0xF0 - 0x10
        ), "response id does not match its command"
    return pairs


if __name__ == "__main__":
    cleanup_mitm_logfile()
    # with open(mitm_clean_logfile, "r") as f:
    with open(mitm_new_logfile, "r") as f:
        tsvdata = f.read()
    pairs = parse_tsvconversation(tsvdata)
    for pair in pairs:
        print(
            pair[0].hex() if pair[0] is not None else None,
            pair[1].hex() if pair[1] is not None else None,
        )

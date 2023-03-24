# logs from the MITM attack, in this format: <Write|Notify>\t<hex data>
# Where hex data is an array of bytes separated by spaces
mitm_clean_logfile = "mitm_clean.log"

def cleanup_mitm_logfile():
    # This function removes all lines where "App to Target" uses "Notify", removes columns 0, 1 and 3. If a command (last column) does not start with "f0", it is appended to the previous line's command
    with open(mitm_clean_logfile, "w") as f:
        with open(mitm_logfile, "r") as g:
            lines = g.readlines()
            for line in lines:
                pass # TODO

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
    # read the tsv file and convert it to a list of (command, response) pairs
    with open(mitm_clean_logfile, "r") as f:
        tsvdata = f.read()
    pairs = parse_tsvconversation(tsvdata)
    for pair in pairs:
        print(
            pair[0].hex() if pair[0] is not None else None,
            pair[1].hex() if pair[1] is not None else None,
        )

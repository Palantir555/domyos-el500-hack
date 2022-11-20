# Useful commands to review nRF conn logs:

```
cat nrf-logs/logs.txt | grep '^A' | grep -o '"(0x.*"' | awk '!x[$0]++' | grep ' F0-BC'
```

# New Conn, no activity log review

Notifications recvd by `nRF Connect` when a new conn is established by the
`eConnected` app:

Received on characteristic `49535343-1e4d-4bd9-ba61-23c647249616`:

```
A  21:54:28.663  "(0x) F0-D9-00-08-36-81-67-EF"
A  21:54:29.090  "(0x) F0-BD-FF-FF-FF-FF-FF-FF-FF-FF-01-FF-FF-FF-FF-FF-FF-FF-01-FF"
A  21:54:29.090  "(0x) FF-FF-9D"
A  21:54:29.140  "(0x) F0-D4-03-C7"
A  21:54:29.260  "(0x) F0-BD-FF-FF-FF-FF-FF-FF-FF-FF-01-FF-FF-FF-FF-FF-FF-FF-01-FF"
A  21:54:29.261  "(0x) FF-FF-9D"
A  21:54:29.380  "(0x) F0-DB-02-00-08-FF-01-00-00-01-01-00-00-00-01-00-00-00-01-00"
A  21:54:29.381  "(0x) 00-00-01-00-00-00-DA"
A  21:54:29.521  "(0x) F0-B3-01-01-FF-FF-A3"
A  21:54:29.580  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:29.580  "(0x) 00-FF-00-00-00-AB"
A  21:54:29.642  "(0x) F0-B3-01-01-FF-FF-A3"
A  21:54:29.720  "(0x) F0-B4-16-11-00-04-DE-FF-FF-FF-FF-FF-A8"
A  21:54:29.802  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:29.803  "(0x) 00-FF-00-00-00-AB"
A  21:54:29.921  "(0x) F0-B4-16-11-00-04-DE-FF-FF-FF-FF-FF-A8"
A  21:54:30.042  "(0x) F0-B5-00-00-FF-FF-A3"
A  21:54:30.101  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:30.102  "(0x) 00-FF-00-00-00-AB"
A  21:54:30.142  "(0x) F0-B5-00-00-FF-FF-A3"
A  21:54:30.201  "(0x) F0-BB-00-00-FF-FF-FF-A8"
A  21:54:30.262  "(0x) F0-BB-00-00-FF-FF-FF-A8"
A  21:54:30.321  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:30.322  "(0x) 00-FF-00-00-00-AB"
A  21:54:30.541  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:30.542  "(0x) 00-FF-00-00-00-AB"
A  21:54:30.824  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:30.825  "(0x) 00-FF-00-00-00-AB"
A  21:54:31.141  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:31.160  "(0x) 00-FF-00-00-00-AB"
A  21:54:31.421  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:31.422  "(0x) 00-FF-00-00-00-AB"
A  21:54:31.720  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:31.720  "(0x) 00-FF-00-00-00-AB"
A  21:54:32.040  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:32.061  "(0x) 00-FF-00-00-00-AB"
A  21:54:32.340  "(0x) F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00"
A  21:54:32.348  "(0x) 00-FF-00-00-00-AB"
```

## Messages by size:

- 6 bytes:
    ```
    FF-FF-9D
    FF-FF-9D
    ```
- 8 bytes:
    ```
    F0-D4-03-C7
    ```
- 12 bytes:
    ```
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    00-FF-00-00-00-AB
    ```
- 14 bytes:
    ```
    00-00-01-00-00-00-DA
    F0-B3-01-01-FF-FF-A3
    F0-B3-01-01-FF-FF-A3
    F0-B5-00-00-FF-FF-A3
    F0-B5-00-00-FF-FF-A3
    ```
- 16 bytes:
    ```
    F0-D9-00-08-36-81-67-EF
    F0-BB-00-00-FF-FF-FF-A8
    F0-BB-00-00-FF-FF-FF-A8
    ```
- 26 bytes:
    ```
    F0-B4-16-11-00-04-DE-FF-FF-FF-FF-FF-A8
    F0-B4-16-11-00-04-DE-FF-FF-FF-FF-FF-A8
    ```
- 40 bytes:
    ```
    F0-BD-FF-FF-FF-FF-FF-FF-FF-FF-01-FF-FF-FF-FF-FF-FF-FF-01-FF
    F0-BD-FF-FF-FF-FF-FF-FF-FF-FF-01-FF-FF-FF-FF-FF-FF-FF-01-FF
    F0-DB-02-00-08-FF-01-00-00-01-01-00-00-00-01-00-00-00-01-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-00-00-00-01-00-01-00-00-00
    ```

## Messages by code:

- `F0-BC` status report:
    ```
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-03-00-01-00-00-00
                                             /__\
                                            Resistance setting
    # sample from activeSessionAcceleratingWalkOnly.txt
    # cat activeSessionAcceleratingWalkOnly.txt | grep '^A' | grep -o '"(0x.*"' | awk '!x[$0]++' | grep ' F0-BC'
    F0-BC-FF-FF-00-00-00-00-00-00-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-16-00-1A-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-1B-00-20-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-1F-00-25-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-25-00-2B-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-27-00-2E-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-29-00-30-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-2C-00-33-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-2F-00-37-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-33-00-3C-00-01-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-35-00-3E-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-33-00-3C-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-31-00-39-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-2D-00-35-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-2C-00-33-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-2B-00-32-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-28-00-2F-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-26-00-2C-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-23-00-29-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-20-00-26-00-02-00-00-03-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-03-00-01-00-00-00
                        /__\  /__\           /__\
                      Speed?  Speed?         Resistance
    # cat nrf-logs/activeSessHeartrateOnly.txt | grep '^A' | grep -o '"(0x.*"' | awk '!x[$0]++'
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-04-00-01-00-00-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-04-00-01-00-55-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-04-00-01-00-53-00
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-04-00-01-00-51-00
                        /__\  /__\           /__\        /__\
                      Speed?  Speed?         Resistance  Heartrate

    # cat nrf-logs/activeSessAllIn.txt | grep '^A' | grep '"(0x.*"' | grep ' F0-BC'
    F0-BC-FF-FF-00-00-00-00-00-00-00-02-00-00-04-00-01-00-00-00" 17:36:30.236
    ...
    F0-BC-FF-FF-00-00-00-2B-00-32-00-02-00-00-04-00-01-00-55-00 - 17:38:40.918
    F0-BC-FF-FF-00-00-00-2B-00-32-00-03-00-00-04-00-01-00-55-00 - 17:38:41.257
    ...
    F0-BC-FF-FF-00-00-00-2C-00-34-00-03-00-00-04-00-01-00-57-00 - 17:38:43.317
    F0-BC-FF-FF-00-00-00-24-00-2A-00-04-00-00-04-00-01-00-53-00 - 17:38:52.319
    ...
    F0-BC-FF-FF-00-00-00-22-00-28-00-04-00-00-05-00-01-00-4B-00 - 17:39:00.757
    F0-BC-FF-FF-00-00-00-22-00-28-00-05-00-00-05-00-01-00-4B-00 - 17:39:01.058
    ...
    F0-BC-FF-FF-00-00-00-16-00-1A-00-05-00-00-04-00-01-00-4B-00 - 17:39:06.758
    ...
    F0-BC-FF-FF-00-00-00-00-00-00-00-05-00-00-04-00-01-00-4B-00 - 17:39:08.298
    F0-BC-FF-FF-00-00-00-00-00-00-00-05-00-00-04-00-01-00-4B-00 - 17:39:08.557

                                    Increases every 10s of activity
                                  ?--__/
    F0-BC-FF-FF-00-00-00-00-00-00-00-05-00-00-04-00-01-00-00-00" 17:39:19.719
                      ?--__/?--__/           \__/      ?--__/
                      Speed?  Speed?         Resistance  Heartrate

    ```

- `22-FF` also a status report? in-session only. Not present on new connection:
    ```
    22-FF-00-00-01-D1 # Sample from buttons only logs
                    T
                    Resistance setting - 1 (??)
    ---------
    # Samples from accelerating walk only logs:
    22-FF-00-00-01-18
    22-FF-00-00-01-1E
    22-FF-00-00-01-24
    22-FF-00-00-01-29
    22-FF-00-00-01-D2
    ```

meta:
  id: response_status
  endian: be
seq:
  - id: head
    type: u1
    doc: Head (0xf0)
  - id: response_identifier
    type: u1
    doc: Response identifier (0xbc)
  - id: unknown1
    type: u2
    doc: Unknown (0xff 0xff)
  - id: unknown2
    type: u2
    doc: Unknown (0x00 0x00)
  - id: rpm_a
    type: u2
    doc: RPM_A (0x00 0x16)
  - id: rpm_b
    type: u2
    doc: RPM_B (0x00 0x16)
  - id: seconds_moving_over_10
    type: u2
    doc: Seconds moving over 10
  - id: minutes_moving
    type: u2
    doc: Minutes moving
  - id: resistance
    type: u1
    doc: Resistance (0x04)
  - id: unknown3
    type: u2
    doc: Unknown (0x00 0x01)
  - id: heart_rate
    type: u2
    doc: Heart rate (0x00 0x43)
  - id: unknown4
    type: u2
    doc: Unknown (0x00 0x00)
  - id: unknown5
    type: u2
    doc: Unknown (0xFF 0x00)
  - id: unknown6
    type: u2
    doc: Unknown (0x00 0x01)
  - id: checksum
    type: u1
    doc: Checksum (Sum of all bytes & 0xff). Indicates end of message

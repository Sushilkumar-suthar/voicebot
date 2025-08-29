# μ-law → PCM16 decoder (for Twilio → Azure STT)
# Ref: ITU-T G.711 μ-law

MU_LAW_EXPAND_TABLE = []
for i in range(256):
    u = ~i & 0xFF
    sign = (u & 0x80)
    exponent = (u >> 4) & 0x07
    mantissa = u & 0x0F
    magnitude = ((mantissa << 3) + 0x84) << exponent
    sample = magnitude - 0x84
    if sign:
        sample = -sample
    MU_LAW_EXPAND_TABLE.append(sample)


def ulaw_bytes_to_pcm16(ulaw: bytes) -> bytes:
    # Return little-endian 16-bit PCM
    out = bytearray()
    for b in ulaw:
        s = MU_LAW_EXPAND_TABLE[b]
        # clamp to int16
        if s > 32767: s = 32767
        if s < -32768: s = -32768
        out += int(s).to_bytes(2, "little", signed=True)
    return bytes(out)
"""
SoilDepth-AI — Sentinel-2 15-Bit TIFF Decoder & Recovery Utility
Author: Senior Remote-Sensing Engineer & ML Data Pipeline Auditor, SoilDepth-AI
Purpose: Decodes ESA Processing Baseline 05.10 Cloud-Optimized GeoTIFFs encoded with
         15-bit integer samples (BitsPerSample = 15, FillOrder = 1 MSB-first)
         that exceed standard Pillow / PIL TIFF decoder support.
"""

import zlib
import numpy as np
from typing import Tuple, Optional


def unpack_15bit_msb(raw_bytes: bytes, num_pixels: Optional[int] = None) -> np.ndarray:
    """
    Unpacks 15-bit MSB-first bit-packed byte buffer into uint16 numpy array.
    In standard TIFF 6.0 MSB bit-packing with BitsPerSample = 15:
    Every 15 bytes contain exactly 8 consecutive 15-bit samples (120 bits total).

    Args:
        raw_bytes: Decompressed Deflate byte buffer from TIFF tile.
        num_pixels: Number of expected pixels (e.g. tile_w * tile_h).

    Returns:
        np.ndarray of dtype uint16 containing unpacked digital numbers.
    """
    # 15 bytes = 120 bits = 8 * 15 bits
    b = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 15)
    n_chunks = b.shape[0]
    out = np.zeros((n_chunks, 8), dtype=np.uint16)

    # p0: 8 bits of b0 + high 7 bits of b1
    out[:, 0] = (b[:, 0].astype(np.uint16) << 7) | (b[:, 1].astype(np.uint16) >> 1)

    # p1: bit 0 of b1 + 8 bits of b2 + high 6 bits of b3
    out[:, 1] = (
        ((b[:, 1].astype(np.uint16) & 0x01) << 14)
        | (b[:, 2].astype(np.uint16) << 6)
        | (b[:, 3].astype(np.uint16) >> 2)
    )

    # p2: bits 1..0 of b3 + 8 bits of b4 + high 5 bits of b5
    out[:, 2] = (
        ((b[:, 3].astype(np.uint16) & 0x03) << 13)
        | (b[:, 4].astype(np.uint16) << 5)
        | (b[:, 5].astype(np.uint16) >> 3)
    )

    # p3: bits 2..0 of b5 + 8 bits of b6 + high 4 bits of b7
    out[:, 3] = (
        ((b[:, 5].astype(np.uint16) & 0x07) << 12)
        | (b[:, 6].astype(np.uint16) << 4)
        | (b[:, 7].astype(np.uint16) >> 4)
    )

    # p4: bits 3..0 of b7 + 8 bits of b8 + high 3 bits of b9
    out[:, 4] = (
        ((b[:, 7].astype(np.uint16) & 0x0F) << 11)
        | (b[:, 8].astype(np.uint16) << 3)
        | (b[:, 9].astype(np.uint16) >> 5)
    )

    # p5: bits 4..0 of b9 + 8 bits of b10 + high 2 bits of b11
    out[:, 5] = (
        ((b[:, 9].astype(np.uint16) & 0x1F) << 10)
        | (b[:, 10].astype(np.uint16) << 2)
        | (b[:, 11].astype(np.uint16) >> 6)
    )

    # p6: bits 5..0 of b11 + 8 bits of b12 + high 1 bit of b13
    out[:, 6] = (
        ((b[:, 11].astype(np.uint16) & 0x3F) << 9)
        | (b[:, 12].astype(np.uint16) << 1)
        | (b[:, 13].astype(np.uint16) >> 7)
    )

    # p7: bits 6..0 of b13 + 8 bits of b14
    out[:, 7] = (
        ((b[:, 13].astype(np.uint16) & 0x7F) << 8)
        | b[:, 14].astype(np.uint16)
    )

    flat = out.ravel()
    if num_pixels is not None:
        flat = flat[:num_pixels]
    return flat


def pack_15bit_msb(pixels: np.ndarray) -> bytes:
    """
    Inverse helper: packs array of 15-bit integers into MSB byte stream.
    Used for unit testing and roundtrip verification.
    """
    pixels = np.asarray(pixels, dtype=np.uint16)
    n = len(pixels)
    pad = (8 - (n % 8)) % 8
    if pad > 0:
        pixels = np.pad(pixels, (0, pad))

    p = pixels.reshape(-1, 8)
    n_chunks = p.shape[0]
    b = np.zeros((n_chunks, 15), dtype=np.uint8)

    b[:, 0] = (p[:, 0] >> 7).astype(np.uint8)
    b[:, 1] = (((p[:, 0] & 0x7F) << 1) | (p[:, 1] >> 14)).astype(np.uint8)
    b[:, 2] = ((p[:, 1] >> 6) & 0xFF).astype(np.uint8)
    b[:, 3] = (((p[:, 1] & 0x3F) << 2) | (p[:, 2] >> 13)).astype(np.uint8)
    b[:, 4] = ((p[:, 2] >> 5) & 0xFF).astype(np.uint8)
    b[:, 5] = (((p[:, 2] & 0x1F) << 3) | (p[:, 3] >> 12)).astype(np.uint8)
    b[:, 6] = ((p[:, 3] >> 4) & 0xFF).astype(np.uint8)
    b[:, 7] = (((p[:, 3] & 0x0F) << 4) | (p[:, 4] >> 11)).astype(np.uint8)
    b[:, 8] = ((p[:, 4] >> 3) & 0xFF).astype(np.uint8)
    b[:, 9] = (((p[:, 4] & 0x07) << 5) | (p[:, 5] >> 10)).astype(np.uint8)
    b[:, 10] = ((p[:, 5] >> 2) & 0xFF).astype(np.uint8)
    b[:, 11] = (((p[:, 5] & 0x03) << 6) | (p[:, 6] >> 9)).astype(np.uint8)
    b[:, 12] = ((p[:, 6] >> 1) & 0xFF).astype(np.uint8)
    b[:, 13] = (((p[:, 6] & 0x01) << 7) | (p[:, 7] >> 8)).astype(np.uint8)
    b[:, 14] = (p[:, 7] & 0xFF).astype(np.uint8)

    return b.tobytes()


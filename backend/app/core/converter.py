"""Audio/video conversion to WAV using ffmpeg."""
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

FFMPEG_TIMEOUT = 300


def convert_to_wav(audio_data: bytes, filename: str) -> bytes:
    """
    Convert any audio/video file to WAV (PCM 16-bit, 16kHz, mono) using ffmpeg.

    Args:
        audio_data: Raw file bytes
        filename: Original filename (for logging and extension detection)

    Returns:
        WAV file bytes

    Raises:
        RuntimeError: If ffmpeg conversion fails
    """
    input_file = None
    output_file = None

    try:
        # Write input to temp file
        _, ext = os.path.splitext(filename)
        input_file = tempfile.NamedTemporaryFile(suffix=ext or '.bin', delete=False)
        input_file.write(audio_data)
        input_file.close()

        # Create output temp file
        output_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        output_file.close()

        # Run ffmpeg
        cmd = [
            'ffmpeg',
            '-i', input_file.name,
            '-y',               # Overwrite output
            '-vn',              # Strip video stream
            '-acodec', 'pcm_s16le',
            '-ar', '16000',     # 16kHz sample rate
            '-ac', '1',         # Mono
            output_file.name,
        ]

        logger.info(f"Converting '{filename}' to WAV via ffmpeg")

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=FFMPEG_TIMEOUT,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            raise RuntimeError(f"ffmpeg failed for '{filename}': {stderr}")

        # Read converted output
        with open(output_file.name, 'rb') as f:
            wav_data = f.read()

        if not wav_data:
            raise RuntimeError(f"ffmpeg produced empty output for '{filename}'")

        logger.info(
            f"Converted '{filename}': {len(audio_data)} bytes -> {len(wav_data)} bytes WAV"
        )
        return wav_data

    finally:
        # Cleanup temp files
        if input_file and os.path.exists(input_file.name):
            os.unlink(input_file.name)
        if output_file and os.path.exists(output_file.name):
            os.unlink(output_file.name)

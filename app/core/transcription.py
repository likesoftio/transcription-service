"""Transcription service using Deepgram API."""
import logging
import io
from typing import Dict, Optional
from deepgram import DeepgramClient, PrerecordedOptions

from app.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize transcription service.
        
        Args:
            api_key: Deepgram API key (defaults to settings.DEEPGRAM_API_KEY)
        """
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        if not self.api_key:
            raise ValueError("Deepgram API key is required")
        self.client = DeepgramClient(self.api_key)
        logger.info("Transcription service initialized")
    
    def transcribe(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        model: str = "nova-2",
        language: str = "ru",
        chunk_duration: float = 30.0,
        diarize: bool = True
    ) -> Optional[Dict]:
        """
        Transcribe audio data using Deepgram API.
        
        Args:
            audio_data: Audio file bytes
            filename: Original filename (for logging)
            model: Deepgram model to use
            language: Language code (default: 'ru')
            chunk_duration: Duration of each chunk in seconds
            diarize: Enable speaker diarization
            
        Returns:
            Dictionary with transcription results or None if error
        """
        try:
            file_size = len(audio_data)
            logger.info(f"Starting Deepgram transcription")
            logger.info(f"  File: {filename}")
            logger.info(f"  Size: {file_size / 1024 / 1024:.2f} MB")
            logger.info(f"  Model: {model}, Language: {language}")
            
            # Configure options
            options = PrerecordedOptions(
                model=model,
                channels=1,  # mono
                punctuate=True,
                diarize=diarize,
                utterances=True if diarize else False,
                language=language,
            )
            
            # Perform transcription using bytes buffer
            audio_buffer = io.BytesIO(audio_data)
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio_buffer},
                options
            )
            
            # Extract results
            result = response.results
            
            if not result or not hasattr(result, 'channels') or not result.channels:
                logger.warning(f"No transcription results for {filename}")
                return None
            
            # Get transcript text
            transcript_text = ""
            if result.channels and len(result.channels) > 0:
                channel = result.channels[0]
                if hasattr(channel, 'alternatives') and channel.alternatives:
                    transcript_text = channel.alternatives[0].transcript
            
            # Count speakers and build speaker-by-speaker transcript
            speaker_count = 0
            speakers_transcript = ""
            chunks_transcript = ""
            speaker_ids = set()
            
            if hasattr(result, 'utterances') and result.utterances:
                # Sort utterances by start time
                utterances_list = []
                for utterance in result.utterances:
                    if hasattr(utterance, 'speaker') and utterance.speaker is not None:
                        speaker_ids.add(utterance.speaker)
                        
                        # Extract text from utterance
                        utterance_text = ""
                        if hasattr(utterance, 'transcript') and utterance.transcript:
                            utterance_text = utterance.transcript
                        elif hasattr(utterance, 'words') and utterance.words:
                            words_list = []
                            for word_obj in utterance.words:
                                if hasattr(word_obj, 'word'):
                                    words_list.append(word_obj.word)
                            utterance_text = " ".join(words_list)
                        
                        start = getattr(utterance, 'start', 0)
                        end = getattr(utterance, 'end', 0)
                        utterances_list.append({
                            'speaker': utterance.speaker,
                            'text': utterance_text,
                            'start': start,
                            'end': end
                        })
                
                speaker_count = len(speaker_ids) if speaker_ids else 0
                
                # Build formatted transcript with speaker labels
                if utterances_list:
                    utterances_list.sort(key=lambda x: x['start'])
                    
                    # Format: "Спикер 0 [00:12.345]: текст реплики"
                    for utt in utterances_list:
                        if utt['text']:
                            start_seconds = utt['start']
                            minutes = int(start_seconds // 60)
                            seconds = start_seconds % 60
                            time_str = f"{minutes:02d}:{seconds:05.2f}"
                            speakers_transcript += f"Спикер {utt['speaker']} [{time_str}]: {utt['text']}\n"
                    
                    speakers_transcript = speakers_transcript.strip()
                    
                    # Build chunks transcript
                    current_chunk_start = 0.0
                    current_chunk_utterances = []
                    
                    for utt in utterances_list:
                        if not utt['text']:
                            continue
                            
                        if utt['start'] >= current_chunk_start + chunk_duration:
                            if current_chunk_utterances:
                                chunk_start_min = int(current_chunk_start // 60)
                                chunk_start_sec = current_chunk_start % 60
                                chunk_end_min = int((current_chunk_start + chunk_duration) // 60)
                                chunk_end_sec = (current_chunk_start + chunk_duration) % 60
                                
                                chunks_transcript += f"\n--- Чанк [{chunk_start_min:02d}:{chunk_start_sec:05.2f} - {chunk_end_min:02d}:{chunk_end_sec:05.2f}] ---\n"
                                
                                for chunk_utt in current_chunk_utterances:
                                    start_seconds = chunk_utt['start']
                                    minutes = int(start_seconds // 60)
                                    seconds = start_seconds % 60
                                    time_str = f"{minutes:02d}:{seconds:05.2f}"
                                    chunks_transcript += f"Спикер {chunk_utt['speaker']} [{time_str}]: {chunk_utt['text']}\n"
                            
                            current_chunk_start = (utt['start'] // chunk_duration) * chunk_duration
                            current_chunk_utterances = []
                        
                        current_chunk_utterances.append(utt)
                    
                    # Finalize last chunk
                    if current_chunk_utterances:
                        chunk_start_min = int(current_chunk_start // 60)
                        chunk_start_sec = current_chunk_start % 60
                        chunk_end = utterances_list[-1]['end'] if utterances_list else current_chunk_start + chunk_duration
                        chunk_end_min = int(chunk_end // 60)
                        chunk_end_sec = chunk_end % 60
                        
                        chunks_transcript += f"\n--- Чанк [{chunk_start_min:02d}:{chunk_start_sec:05.2f} - {chunk_end_min:02d}:{chunk_end_sec:05.2f}] ---\n"
                        
                        for chunk_utt in current_chunk_utterances:
                            start_seconds = chunk_utt['start']
                            minutes = int(start_seconds // 60)
                            seconds = start_seconds % 60
                            time_str = f"{minutes:02d}:{seconds:05.2f}"
                            chunks_transcript += f"Спикер {chunk_utt['speaker']} [{time_str}]: {chunk_utt['text']}\n"
                    
                    chunks_transcript = chunks_transcript.strip()
            
            # Get duration
            duration = None
            if hasattr(result, 'metadata') and result.metadata:
                if hasattr(result.metadata, 'duration'):
                    duration = result.metadata.duration
            
            logger.info(f"Transcription completed")
            logger.info(f"  Characters: {len(transcript_text):,}")
            logger.info(f"  Speakers: {speaker_count}")
            if duration:
                logger.info(f"  Duration: {duration:.2f} seconds")
            
            return {
                'transcript': transcript_text,
                'speakers_transcript': speakers_transcript,
                'chunks_transcript': chunks_transcript,
                'speaker_count': speaker_count,
                'duration': duration,
            }
        
        except Exception as e:
            logger.error(f"Error transcribing {filename}: {e}", exc_info=True)
            return None


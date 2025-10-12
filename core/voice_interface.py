"""
Voice interface for Joi
Speech-to-text and text-to-speech capabilities
"""

import os
import io
import base64
from typing import Optional, Dict
import speech_recognition as sr
from elevenlabs import ElevenLabs, Voice, VoiceSettings
import pygame
from loguru import logger

class VoiceInterface:
    """Manages voice input/output for Joi"""
    
    def __init__(self):
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # ElevenLabs for TTS
        self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        self.elevenlabs_client = None
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Default to "Bella"
        
        if self.elevenlabs_key:
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_key)
            logger.info("ElevenLabs TTS initialized")
        else:
            logger.warning("No ElevenLabs API key - using system TTS")
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """Listen for voice input and convert to text"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening...")
                
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout)
                
                # Recognize using Google's free API (can switch to other providers)
                try:
                    text = self.recognizer.recognize_google(audio)
                    logger.info(f"Recognized: {text}")
                    return text
                except sr.UnknownValueError:
                    logger.warning("Could not understand audio")
                    return None
                except sr.RequestError as e:
                    logger.error(f"Recognition service error: {e}")
                    return None
                    
        except sr.WaitTimeoutError:
            logger.info("Listening timeout - no speech detected")
            return None
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None
    
    def speak_elevenlabs(self, text: str) -> bool:
        """Speak text using ElevenLabs high-quality voice"""
        if not self.elevenlabs_client:
            return self.speak_system(text)
        
        try:
            # Generate audio with ElevenLabs
            audio = self.elevenlabs_client.generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(
                        stability=0.75,
                        similarity_boost=0.85,
                        style=0.5,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_turbo_v2"  # Fast and high quality
            )
            
            # Convert generator to bytes
            audio_bytes = b''.join(audio)
            
            # Play audio using pygame
            audio_stream = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(audio_stream)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            return True
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return self.speak_system(text)
    
    def speak_system(self, text: str) -> bool:
        """Fallback to system TTS"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Configure voice properties
            voices = engine.getProperty('voices')
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 175)  # Speed
            engine.setProperty('volume', 0.9)  # Volume
            
            engine.say(text)
            engine.runAndWait()
            return True
            
        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return False
    
    def speak(self, text: str) -> bool:
        """Main speak method - uses best available option"""
        if self.elevenlabs_client:
            return self.speak_elevenlabs(text)
        else:
            return self.speak_system(text)
    
    def get_available_voices(self) -> Dict:
        """Get list of available voices"""
        voices = {'system': [], 'elevenlabs': []}
        
        # System voices
        try:
            import pyttsx3
            engine = pyttsx3.init()
            for voice in engine.getProperty('voices'):
                voices['system'].append({
                    'id': voice.id,
                    'name': voice.name
                })
        except:
            pass
        
        # ElevenLabs voices
        if self.elevenlabs_client:
            try:
                # This would need actual API call to list voices
                voices['elevenlabs'] = [
                    {'id': 'EXAVITQu4vr4xnSDxMaL', 'name': 'Bella'},
                    {'id': 'MF3mGyEYCl7XYWbV9V6O', 'name': 'Elli'},
                    {'id': 'XB0fDUnXU5powFXDhCwa', 'name': 'Charlotte'},
                ]
            except:
                pass
        
        return voices
    
    def set_voice(self, voice_id: str):
        """Change the TTS voice"""
        self.voice_id = voice_id
        logger.info(f"Voice changed to: {voice_id}")

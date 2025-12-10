import os
import wave
import tempfile
import shutil
import base64
from pydub import AudioSegment
from typing import Optional, Tuple, Union
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, TCOM, TCON, TDRC, TRCK, TPOS, TYER


class Audio_Hider:
    SUPPORTED_FORMATS = {
        '.wav': 'wav',
        '.mp3': 'mp3',    # MP3 format
        '.aac': 'adts',   # AAC in ADTS container
        '.flac': 'flac',  # FLAC format
        '.alac': 'ipod',  # ALAC in M4A container
        '.aif': 'aiff',   # AIFF
        '.aiff': 'aiff',  # AIFF (alternative extension)
        '.dsf': 'dsf',    # DSD
        '.pcm': 'wav',    # Raw PCM will be handled as WAV
        '.m4a': 'ipod',   # M4A format (AAC in MP4 container)
        '.ogg': 'ogg',    # OGG Vorbis
        '.wma': 'asf'     # Windows Media Audio
    }
    
    def __init__(self, host_file, hidden_data):
        """
        Initialize the Audio_Hider with host file and data to hide.
        
        Args:
            host_file: File object containing the host audio file info
            hidden_data: Data to hide in the audio file
        """
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.temp_path = "temp_files/"
        self.output_path = "output_files/"
        self.end_marker = "#END_OF_MESSAGE#"
        
        # Create necessary directories if they don't exist
        os.makedirs(self.temp_path, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)
    
    def _get_file_extension(self, file_path) -> str:
        """Get the lowercase file extension with leading dot."""
        # If it's a File object, get the extension from the attribute
        if hasattr(file_path, 'file_extension'):
            ext = file_path.file_extension.lower()
            # Ensure the extension has a leading dot if it's not empty
            return f'.{ext}' if ext and not ext.startswith('.') else ext
        # If it's a string path, use os.path to get the extension
        elif isinstance(file_path, str):
            ext = os.path.splitext(file_path)[1].lower()
            # Ensure the extension has a leading dot if it's not empty
            return f'.{ext}' if ext and not ext.startswith('.') else ext
        else:
            return ''
    
    def _get_format_from_extension(self, file_path: str) -> Optional[str]:
        """Get the format string for pydub based on file extension."""
        ext = self._get_file_extension(file_path)
        return self.SUPPORTED_FORMATS.get(ext)
    
    def _convert_to_wav(self, input_path: str) -> str:
        """Convert any supported audio format to WAV for processing."""
        if self._get_file_extension(input_path) == '.wav':
            return input_path
            
        output_path = os.path.join(self.temp_path, 'temp_audio.wav')
        audio_format = self._get_format_from_extension(input_path)
        print(audio_format)
        print(input_path)
        
        if not audio_format:
            raise ValueError(f"Unsupported audio format: {input_path}")
            
        audio = AudioSegment.from_file(input_path, format=audio_format)
        audio.export(output_path, format='wav')
        return output_path
    
    def _convert_from_wav(self, wav_path: str, output_path: str) -> None:
        """Convert WAV back to the original format with high quality settings.
        
        Args:
            wav_path: Path to the source WAV file
            output_path: Path where to save the converted file
        """
        target_format = self._get_format_from_extension(output_path)
        
        if not target_format:
            raise ValueError(f"Unsupported output format: {output_path}")
            
        audio = AudioSegment.from_wav(wav_path)
        
        # Common export parameters for all formats
        export_params = {
            'format': target_format,
            'parameters': ['-y']  # Overwrite output file if it exists
        }
    
        # Special handling for different formats
        if target_format == 'adts':  # AAC
            export_params.update({
                'codec': 'aac',
                'bitrate': '320k',
                'parameters': ['-profile:a', 'aac_he_v2', '-q:a', '0']
            })
        elif target_format == 'mp3':
            export_params.update({
                'codec': 'libmp3lame',
                'bitrate': '320k',
                'parameters': ['-q:a', '0', '-joint_stereo', '0']
            })
        elif target_format == 'ipod':  # ALAC
            export_params.update({
                'codec': 'alac',
                'parameters': ['-compression_level', '0']
            })
        elif target_format == 'flac':
            export_params.update({
                'codec': 'flac',
                'compression_level': '8'
            })
        elif target_format == 'aiff':
            export_params.update({
                'codec': 'pcm_s16be',  # 16-bit big-endian PCM
                'bitrate': '1411k'  # CD quality
            })
        elif target_format == 'wav':
            export_params.update({
                'codec': 'pcm_s16le',  # 16-bit little-endian PCM
                'bitrate': '1411k'  # CD quality
            })
        
        # For DSD, we'll still need to handle it specially
        if target_format == 'dsf':
            # DSD is a special case, we'll convert to WAV first then use external tools
            temp_wav = os.path.join(self.temp_path, 'temp_dsd.wav')
            audio.export(temp_wav, format='wav')
            # Here you would typically call an external tool to convert WAV to DSD
            # For now, we'll just copy the WAV file as a placeholder
            shutil.copy2(temp_wav, output_path)
            print("Warning: DSD output is not fully implemented. Output is WAV format.")
            return
        
        # Export with the appropriate parameters
        try:
            audio.export(output_path, **export_params)
        except Exception as e:
            # Fallback to default export if high-quality export fails
            print(f"Warning: High-quality export failed, falling back to default settings: {str(e)}")
            audio.export(output_path, format=target_format)

    def convert_data_to_binary(self, data: Union[str, bytes]) -> str:
        """Convert data to binary string.
        
        Args:
            data: The data to convert (string or bytes)
            
        Returns:
            str: Binary string representation of the data
        """
        if isinstance(data, str):
            return ''.join(format(ord(c), '08b') for c in data)
        elif isinstance(data, bytes):
            return ''.join(format(byte, '08b') for byte in data)
        else:
            raise ValueError("Data must be string or bytes")

    def convert_binary_to_data(self, bits: str) -> str:
        """Convert binary string back to text."""
        chars = [bits[i:i + 8] for i in range(0, len(bits), 8)]
        return ''.join(chr(int(b, 2)) for b in chars)

    def _encode_audio(self, input_path: str, output_path: str) -> None:
        """
        Encode hidden data into the audio file using LSB steganography.
        
        Args:
            input_path: Path to the input audio file
            output_path: Path to save the steganographic audio file
            
        Raises:
            ValueError: If the audio file is too small to hide the data
        """
        # Convert to WAV if needed
        wav_path = self._convert_to_wav(input_path)
        
        # Add null terminator to mark end of data
        if isinstance(self.hidden_data, str):
            data_with_marker = self.hidden_data + '\x00'
        else:
            data_with_marker = self.hidden_data + b'\x00'
            
        bits = self.convert_data_to_binary(data_with_marker)
        
        # Process the WAV file
        with wave.open(wav_path, 'rb') as audio:
            params = audio.getparams()
            frames = bytearray(list(audio.readframes(audio.getnframes())))
        
        # Check if audio is large enough to hide the data
        if len(bits) > len(frames):
            raise ValueError(f"Audio file is too small to hide the data. "
                           f"Needed: {len(bits)} bytes, Available: {len(frames)} bytes")
        
        # Embed the data in the LSB of each sample
        for i, bit in enumerate(bits):
            # Clear the LSB and set it to our data bit
            frames[i] = (frames[i] & 0xFE) | int(bit)
        
        # Save as WAV first
        temp_wav = os.path.join(self.temp_path, 'temp_encoded.wav')
        with wave.open(temp_wav, 'wb') as out_audio:
            out_audio.setparams(params)
            out_audio.writeframes(bytes(frames))
        
        # Convert back to original format if needed
        if self._get_file_extension(input_path) != '.wav':
            self._convert_from_wav(temp_wav, output_path)
        else:
            shutil.copy2(temp_wav, output_path)
            
        # Clean up temporary WAV file
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
    
    def _hide_in_metadata(self, input_path: str, output_path: str) -> bool:
        """
        Hide data in the audio file's metadata.
        
        Args:
            input_path: Path to the input audio file
            output_path: Path to save the modified audio file
            
        Returns:
            bool: True if metadata hiding was successful, False otherwise
        """
        try:
            # Encode the data in base64 to ensure it's safe for metadata
            encoded_data = base64.b64encode(self.hidden_data.encode('utf-8')).decode('utf-8')
            
            # Copy the original file to the output path first
            shutil.copy2(input_path, output_path)
            
            # Use mutagen to update metadata
            audio = MutagenFile(output_path, easy=True)
            
            # For ID3 tags (MP3, etc.)
            if hasattr(audio, 'tags'):
                if audio.tags is None:
                    audio.add_tags()
                # Store in a custom tag
                audio.tags[self.metadata_key] = encoded_data
            # For other formats that support Vorbis comments (FLAC, OGG, etc.)
            elif hasattr(audio, 'tags'):
                audio.tags[self.metadata_key] = [encoded_data]
            else:
                return False
                
            audio.save()
            return True
            
        except Exception as e:
            print(f"Warning: Failed to hide data in metadata: {str(e)}")
            return False

    def _extract_from_metadata(self, file_path: str) -> Optional[str]:
        """
        Extract hidden data from the audio file's metadata.
        
        Args:
            file_path: Path to the audio file with hidden data
            
        Returns:
            str: The extracted data, or None if no data was found
        """
        try:
            audio = MutagenFile(file_path, easy=True)
            
            # Check ID3 tags first
            if hasattr(audio, 'tags') and audio.tags:
                if self.metadata_key in audio.tags:
                    encoded_data = audio.tags[self.metadata_key]
                    if isinstance(encoded_data, list):
                        encoded_data = encoded_data[0]
                    return base64.b64decode(encoded_data).decode('utf-8')
            
            # Check Vorbis comments
            if hasattr(audio, 'tags') and audio.tags and self.metadata_key in audio.tags:
                encoded_data = audio.tags[self.metadata_key][0]
                return base64.b64decode(encoded_data).decode('utf-8')
                
        except Exception as e:
            print(f"Warning: Failed to extract data from metadata: {str(e)}")
            
        return None

    def hide_data(self) -> None:
        """
        Hide data in the host audio file and save to the output location.
        """
        temp_input_wav = os.path.join(self.temp_path, "temp_input.wav")
        temp_output_wav = os.path.join(self.temp_path, "temp_output.wav")

        # Convert to WAV if needed
        if self.host_file.file_extension.lower() in ['mp3', 'aac', 'm4a', 'flac', 'alac', 'aif', 'aiff', 'dsf', 'pcm']:
            audio_format = self._get_format_from_extension(self.host_file.file_path)
            if audio_format:
                AudioSegment.from_file(self.host_file.file_path, format=audio_format).export(temp_input_wav, format="wav")
            else:
                temp_input_wav = self.host_file.file_path
        else:
            temp_input_wav = self.host_file.file_path

        # Encode the data into the WAV file
        self._encode_audio(temp_input_wav, temp_output_wav)

        # Determine output path
        base_name = os.path.splitext(self.host_file.file_name)[0]
        output_file = os.path.join(self.output_path, f"{base_name}_stego.wav")
        
        # Move the output file to the final location
        if os.path.exists(output_file):
            os.remove(output_file)
        os.rename(temp_output_wav, output_file)

        # Clean up temporary files
        for f in [temp_input_wav]:
            if os.path.exists(f) and f != self.host_file.file_path:
                try:
                    os.remove(f)
                except PermissionError:
                    pass
    
    def extract_data(self) -> str:
        """
        Extract hidden data from the steganographic audio file.
        
        Returns:
            str: The extracted hidden data
        """
        os.makedirs(self.temp_path, exist_ok=True)
        temp_wav = os.path.join(self.temp_path, "temp_decode.wav")
        used_temp = False

        # Convert to WAV if needed
        if self.host_file.file_extension.lower() in ['mp3', 'aac', 'm4a', 'flac', 'alac', 'aif', 'aiff', 'dsf', 'pcm']:
            audio_format = self._get_format_from_extension(self.host_file.file_path)
            if audio_format:
                AudioSegment.from_file(self.host_file.file_path, format=audio_format).export(temp_wav, format="wav")
                used_temp = True
            else:
                temp_wav = self.host_file.file_path
        else:
            temp_wav = self.host_file.file_path

        try:
            # Try to extract from metadata first for lossy formats
            if self.host_file.file_extension.lower() in ['mp3', 'aac', 'm4a']:
                metadata_data = self._extract_from_metadata(temp_wav if used_temp else self.host_file.file_path)
                if metadata_data:
                    return metadata_data
                print("No data found in metadata, trying LSB extraction")
            
            # Read the WAV file
            with wave.open(temp_wav, 'rb') as audio:
                frames = bytearray(list(audio.readframes(audio.getnframes())))
            
            # Extract LSBs - one bit per sample
            bits = []
            data = bytearray()
            
            for byte in frames:
                # Get LSB of current byte
                bits.append(str(byte & 1))
                
                # If we have at least 8 bits, process them
                if len(bits) >= 8:
                    # Convert 8 bits to a byte
                    byte_str = ''.join(bits[:8])
                    byte_val = int(byte_str, 2)
                    data.append(byte_val)
                    bits = bits[8:]
                    
                    # Check for end marker
                    if data.endswith(self.end_marker.encode('utf-8')):
                        # Remove the end marker before returning
                        return data[:-len(self.end_marker)].decode('utf-8', errors='replace')
            
            # If we get here, we didn't find the end marker
            if data:
                return data.decode('utf-8', errors='replace')
                
            return ""
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract data from audio: {str(e)}")
        finally:
            # Clean up temporary files
            if used_temp and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except PermissionError:
                    pass
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """
        Check if the given file has a supported audio format.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            bool: True if the format is supported, False otherwise
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in Audio_Hider.SUPPORTED_FORMATS
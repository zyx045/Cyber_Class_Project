import os
import cv2
import numpy as np
import tempfile
from mutagen.mp4 import MP4
from mutagen import File as MutagenFile  # General purpose Mutagen file handler

class Video_Hider:
    # Define which formats support metadata (only MP4/MOV for now)
    METADATA_FORMATS = {'mp4', 'm4v', 'mov'}
    METADATA_TAG = 'steganography_data'
    
    def __init__(self, host_file, hidden_data=None):
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.output_path = "output_files/"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)

    def _get_metadata_handler(self, file_path):
        """Get the appropriate metadata handler for the file type."""
        ext = self.host_file.file_extension.lower()
        try:
            if ext in self.METADATA_FORMATS:
                # For MP4 files, we need to use the MP4 handler specifically
                if ext in ['mp4', 'm4v']:
                    return MP4(file_path)
                # For other formats, use the generic handler
                return MutagenFile(file_path)
            return None
        except Exception as e:
            print(f"Warning: Could not create metadata handler: {e}")
            return None
            
    def _encode_lsb(self, frame, data):
        """Encode data into the least significant bits of the frame (for lossless formats)."""
        # Convert data to binary and add termination marker
        binary_data = ''.join(format(byte, '08b') for byte in data) + '00000000'  # Null terminator
        
        # Flatten the frame and ensure we have enough space
        flat_frame = frame.flatten()
        max_bits = len(flat_frame) * 2  # Using 2 LSBs per channel
        
        if len(binary_data) > max_bits:
            raise ValueError(f"Data too large for video frame. Max: {max_bits//8} bytes")
        
        # Encode data in the frame
        for i in range(len(binary_data) // 2):
            # Get the next 2 bits of data
            bits = binary_data[i*2:(i+1)*2].ljust(2, '0')
            
            # Clear the 2 LSBs and set them to our data bits
            flat_frame[i] = (flat_frame[i] & 0xFC) | int(bits, 2)
        
        return flat_frame.reshape(frame.shape)
    
    def _decode_lsb(self, frame):
        """Extract data from the least significant bits of the frame."""
        flat_frame = frame.flatten()
        binary_data = ''
        
        # Read 2 LSBs from each channel until we find the null terminator
        for i in range(0, len(flat_frame), 2):
            # Get 2 LSBs and convert to binary string
            lsb = flat_frame[i] & 0x03  # Get last 2 bits
            binary_data += f"{lsb:02b}"
            
            # Check for null terminator (8 consecutive zeros)
            if len(binary_data) >= 8 and binary_data[-8:] == '00000000':
                break
        
        # Convert binary data to bytes
        data = bytearray()
        for i in range(0, len(binary_data)-8, 8):  # Skip the null terminator
            byte = binary_data[i:i+8]
            data.append(int(byte, 2))
        
        return bytes(data) if data else b''

    def hide_data(self):
        """Hide data in the video, using metadata for lossy formats and LSB for lossless."""
        if not self.hidden_data:
            raise ValueError("No data provided to hide")
            
        # Create output filename with _stego suffix
        base_name = os.path.splitext(self.host_file.file_name)[0]
        output_file = os.path.join(self.output_path, f"{base_name}_stego{os.path.splitext(self.host_file.file_name)[1]}")
        
        # For formats that support metadata
        if self.host_file.file_extension.lower() in self.METADATA_FORMATS:
            # First, copy the file to the output location
            import shutil
            shutil.copy2(self.host_file.file_path, output_file)
            
            # Now add metadata
            try:
                handler = self._get_metadata_handler(output_file)
                if not handler:
                    raise ValueError(f"Unsupported video format for metadata: {self.host_file.file_extension}")
                
                # Convert data to string if it's bytes
                data_str = self.hidden_data if isinstance(self.hidden_data, str) else self.hidden_data.decode('utf-8', errors='replace')
                
                # For MP4 files, use the '\xa9xyz' format for custom tags
                if isinstance(handler, MP4):
                    handler.tags['\xa9cmt'] = data_str  # Using comment field for storage
                else:
                    # For other formats, try to use our custom tag
                    try:
                        handler.tags[self.METADATA_TAG] = data_str
                    except Exception:
                        # If custom tag fails, use a standard field
                        handler.tags['comment'] = data_str
                
                handler.save()
                return output_file
                
            except Exception as e:
                # If metadata fails, try LSB as fallback
                print(f"Warning: Metadata storage failed, falling back to LSB: {e}")
                self.is_lossy = False
        
        # For lossless formats or if metadata failed, use LSB
        video = cv2.VideoCapture(self.host_file.file_path)
        
        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Get audio stream information
        has_audio = False
        audio_stream = None
        
        # Try to extract audio using ffmpeg if available
        if shutil.which('ffmpeg'):
            try:
                import subprocess
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio.close()
                
                # Extract audio using ffmpeg
                subprocess.run([
                    'ffmpeg', '-y', '-i', self.host_file.file_path,
                    '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                    temp_audio.name
                ], check=True, capture_output=True)
                
                if os.path.exists(temp_audio.name) and os.path.getsize(temp_audio.name) > 0:
                    has_audio = True
                    audio_stream = temp_audio.name
            except Exception as e:
                print(f"Warning: Could not extract audio: {e}")
                if os.path.exists(temp_audio.name):
                    os.remove(temp_audio.name)
        
        # Read the first frame
        ret, frame = video.read()
        if not ret:
            raise ValueError("Could not read video file")
        
        # Convert data to bytes if it's a string
        data_bytes = self.hidden_data if isinstance(self.hidden_data, bytes) else self.hidden_data.encode('utf-8')
        
        # Encode data in the first frame
        frame_with_data = self._encode_lsb(frame, data_bytes)
        
        # Create a temporary file for the output video
        temp_output = tempfile.NamedTemporaryFile(suffix=os.path.splitext(self.host_file.file_name)[1], delete=False)
        temp_output.close()
        
        # Get the original codec and create VideoWriter with the same properties
        fourcc = int(video.get(cv2.CAP_PROP_FOURCC))
        is_color = len(frame.shape) == 3 and frame.shape[2] > 1
        out = cv2.VideoWriter(
            temp_output.name,
            fourcc,
            fps,
            (width, height),
            is_color
        )
        
        out.write(frame_with_data)
        
        # Write the rest of the frames
        while True:
            ret, frame = video.read()
            if not ret:
                break
            out.write(frame)
        
        # Release resources
        video.release()
        out.release()
        
        # If we have audio, merge it with the video
        final_output = temp_output.name
        if has_audio and audio_stream:
            try:
                temp_with_audio = tempfile.NamedTemporaryFile(suffix=os.path.splitext(self.host_file.file_name)[1], delete=False)
                temp_with_audio.close()
                
                # Use ffmpeg to merge video and audio
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', temp_output.name,  # Video input
                    '-i', audio_stream,      # Audio input
                    '-c:v', 'copy',          # Copy video stream
                    '-c:a', 'aac',           # Encode audio as AAC
                    '-strict', 'experimental',
                    '-map', '0:v:0',         # Use video from first input
                    '-map', '1:a:0',         # Use audio from second input
                    '-shortest',             # Match the shorter of the inputs
                    temp_with_audio.name
                ], check=True, capture_output=True)
                
                final_output = temp_with_audio.name
            except Exception as e:
                print(f"Warning: Could not merge audio: {e}")
        
        # Move the temporary file to the final location
        if os.path.exists(output_file):
            os.remove(output_file)  # Remove if output file already exists
        shutil.move(final_output, output_file)
        
        # Clean up temporary files
        if has_audio and audio_stream and os.path.exists(audio_stream):
            os.remove(audio_stream)
        if os.path.exists(temp_output.name):
            os.remove(temp_output.name)
        
        # Copy original file metadata if possible
        try:
            if shutil.which('ffmpeg'):
                # Use ffmpeg to copy metadata if available
                temp_meta = tempfile.NamedTemporaryFile(suffix=os.path.splitext(self.host_file.file_name)[1], delete=False)
                temp_meta.close()
                try:
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', self.host_file.file_path,  # Source for metadata
                        '-i', output_file,               # Source for content
                        '-map', '1',                    # Use all streams from second input
                        '-map_metadata', '0',           # Copy metadata from first input
                        '-c', 'copy',                   # Stream copy (no re-encoding)
                        temp_meta.name
                    ], check=True, capture_output=True)
                    shutil.move(temp_meta.name, output_file)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    if os.path.exists(temp_meta.name):
                        os.remove(temp_meta.name)
                    print(f"Warning: Could not copy metadata: {e}")
        except Exception as e:
            print(f"Warning: Error during metadata copy: {e}")
        
        return output_file

    def extract_data(self):
        """Extract data from the video, checking metadata first, then LSB."""
        # First try metadata for supported formats
        if self.host_file.file_extension.lower() in self.METADATA_FORMATS:
            try:
                handler = self._get_metadata_handler(self.host_file.file_path)
                if handler:
                    # Check the same fields we might have used to store the data
                    if isinstance(handler, MP4) and '\xa9cmt' in handler.tags:
                        return handler.tags['\xa9cmt'][0]  # Return first comment
                    elif hasattr(handler, 'tags') and self.METADATA_TAG in handler.tags:
                        return handler.tags[self.METADATA_TAG]
                    elif hasattr(handler, 'tags') and 'comment' in handler.tags:
                        return handler.tags['comment']
            except Exception as e:
                print(f"Warning: Metadata extraction failed, trying LSB: {e}")
        
        # If metadata not found or failed, try LSB
        video = cv2.VideoCapture(self.host_file.file_path)
        
        # Read the first frame
        ret, frame = video.read()
        video.release()
        
        if not ret:
            return "(Error reading video file)"
        
        # Extract data from the frame
        data = self._decode_lsb(frame)
        return data.decode('utf-8', errors='replace') if data else "(No hidden message found)"


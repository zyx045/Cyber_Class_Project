import os
from PIL import Image, PngImagePlugin, JpegImagePlugin, GifImagePlugin, BmpImagePlugin, TiffImagePlugin, WebPImagePlugin
from PIL.ExifTags import TAGS

class Image_Hider:
    def __init__(self, host_file, hidden_data):
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.output_path = "output_files/"
        self.working_image = None
        self.is_lossy = self.is_lossy_format()
        self.load_image()

    def is_lossy_format(self):
        """Check if the image format is lossy."""
        lossy_extensions = {'jpg', 'jpeg', 'webp'}
        return self.host_file.file_extension.lower() in lossy_extensions

    def convert_data_to_binary(self, data=None):
        """Convert text to list of binary strings, 8 bits per character.
        
        Args:
            data: The data to convert. If None, uses self.hidden_data
            
        Returns:
            list: List of 8-bit binary strings
        """
        if data is None:
            data = self.hidden_data
        if isinstance(data, str):
            return [format(ord(char), '08b') for char in data]
        elif isinstance(data, bytes):
            return [format(byte, '08b') for byte in data]
        else:
            raise ValueError("Data must be string or bytes")

    def load_image(self):
        os.makedirs(self.output_path, exist_ok=True)
        self.working_image = Image.open(self.host_file.file_path)
        return self.working_image

    def output_image(self):
        output_file_path = os.path.join(self.output_path, self.host_file.file_name)
        if self.is_lossy:
            # For lossy formats, ensure we save with the same quality and other parameters
            self.working_image.save(output_file_path, quality=95, optimize=True, 
                                 exif=self.working_image.info.get('exif', b''))
        else:
            # For lossless formats, preserve all metadata
            self.working_image.save(output_file_path, optimize=True)
        return output_file_path

    def modify_pixel(self, pix):
        """Modify pixel data using LSB steganography for lossless formats."""
        # Add end marker to the data
        data_with_marker = self.hidden_data + '\x00'  # Null byte as end marker
        datalist = self.convert_data_to_binary(data_with_marker)
        lendata = len(datalist)
        imdata = iter(pix)
        
        # Process pixels in chunks of 3 (RGB)
        for i in range(0, len(datalist), 3):
            # Get next 3 bytes (24 bits) or remaining data
            chunk = datalist[i:i+3]
            
            # Get next 3 pixels (9 values, but we'll use 8 bits per 3 pixels)
            try:
                pixels = []
                for _ in range(3):  # Get 3 pixels (9 values)
                    pixels.extend(next(imdata)[:3])
                
                # Modify LSBs of first 8 values
                for j in range(min(8, len(chunk) * 8)):
                    byte_idx = j // 8
                    bit_idx = 7 - (j % 8)  # Most significant bit first
                    
                    if byte_idx < len(chunk) and len(chunk[byte_idx]) > 0:
                        bit = chunk[byte_idx][bit_idx]
                        # Set LSB to match data bit
                        if bit == '1':
                            pixels[j] |= 1
                        else:
                            pixels[j] &= ~1
                
                # Ensure last bit of last pixel in chunk indicates if more data follows
                if i + 3 >= len(datalist):
                    pixels[-1] |= 1  # End of message
                else:
                    pixels[-1] &= ~1  # More data follows
                
                # Yield the modified pixels
                for k in range(0, 9, 3):
                    yield tuple(pixels[k:k+3])
                    
            except StopIteration:
                # Handle case where we run out of pixels
                raise ValueError("Image too small to hide the data")
            
    def hide_in_metadata(self):
        """Hide data in image metadata for lossy formats."""
        try:
            # Create a copy of the existing metadata
            metadata = {}
            if hasattr(self.working_image, 'info'):
                metadata = self.working_image.info.copy()
            
            # Use a custom tag to store our hidden data
            metadata['hidden_data'] = self.hidden_data
            
            # For JPEG, we can also use EXIF data
            if self.host_file.file_extension.lower() in ['jpg', 'jpeg']:
                exif_data = self.working_image.info.get('exif', b'')
                if exif_data:
                    # If there's existing EXIF data, keep it
                    metadata['exif'] = exif_data
            
            # Update the image info
            self.working_image.info = metadata
            return True
            
        except Exception as e:
            print(f"Error hiding data in metadata: {str(e)}")
            return False

    def hide_data(self):
        if self.is_lossy:
            # For lossy formats, use metadata hiding
            if not self.hide_in_metadata():
                raise Exception("Failed to hide data in image metadata")
        else:
            # For lossless formats, use LSB steganography
            w, h = self.working_image.size
            x, y = 0, 0

            for pixel in self.modify_pixel(self.working_image.getdata()):
                self.working_image.putpixel((x, y), pixel)
                x += 1
                if x >= w:
                    x = 0
                    y += 1
                if y >= h:
                    break

        # Save the modified image
        return self.output_image()

    def extract_data(self):
        """Extract hidden data from the image.
        
        Returns:
            str: The extracted data, or empty string if no data found.
        """
        # First try to extract from metadata (for lossy formats)
        if self.is_lossy:
            try:
                # Check for our custom metadata
                if hasattr(self.working_image, 'info') and 'hidden_data' in self.working_image.info:
                    return self.working_image.info['hidden_data']
                
                # For JPEG, also check EXIF data
                if self.host_file.file_extension.lower() in ['jpg', 'jpeg'] and 'exif' in self.working_image.info:
                    # In a real implementation, you would parse the EXIF data here
                    # This is a simplified version
                    exif_data = self.working_image.info['exif']
                    # Look for hidden data in EXIF (this is a placeholder)
                    # You would need to implement proper EXIF parsing
                    pass
            except Exception as e:
                print(f"Error extracting from metadata: {str(e)}")
        
        # If not found in metadata or not a lossy format, try LSB extraction
        imgdata = iter(self.working_image.getdata())
        bits = ''
        data = bytearray()
        
        try:
            while True:
                # Read 3 pixels (9 values)
                pixels = []
                for _ in range(3):
                    pixels.extend(next(imgdata)[:3])
                
                # Extract LSBs from first 8 values (1 bit per value)
                for j in range(8):
                    bits += '1' if (pixels[j] & 1) else '0'
                    
                    # If we have a complete byte, process it
                    if len(bits) >= 8:
                        byte = int(bits[:8], 2)
                        data.append(byte)
                        bits = bits[8:]
                        
                        # Check for null terminator
                        if byte == 0:
                            # Remove the null terminator before returning
                            return data[:-1].decode('utf-8', errors='replace')
                
                # Check if this is the last chunk
                if pixels[-1] & 1:
                    break
                    
        except StopIteration:
            pass  # End of image data
            
        # If we get here, we didn't find a null terminator
        if data:
            return data.decode('utf-8', errors='replace')
        return ""

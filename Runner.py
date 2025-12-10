from objects.File import File
from Audio_Hider import Audio_Hider
from Image_Hider import Image_Hider
from Video_Hider import Video_Hider
from File_Handeler import File_Handeler

class Runner:
    def __init__(self):
        self.output_path = "output_files/"
        # Salt for key derivation - should be the same for encryption and decryption
        self.salt = b'salt_'  # In production, this should be randomly generated and stored securely


    def proccess_hidden_file(self, hidden_file, carrier_files, carrier_percentages=None):
        # Convert content to string
        content = str(hidden_file.file_content)
        
        # Prepare chunks
        content_chunks = []
        carrier_count = len(carrier_files)
        content_length = len(content)
        
        # If no percentages provided, distribute evenly
        if carrier_percentages is None:
            carrier_percentages = [100.0 / carrier_count] * carrier_count
        
        # If content is smaller than number of carriers, adjust carrier count
        if content_length < carrier_count:
            carrier_count = content_length or 1  # Ensure at least 1 carrier
        
        # Calculate chunk sizes based on percentages
        chunk_sizes = []
        remaining = content_length
        
        # Calculate sizes for all chunks except the last one
        for i in range(carrier_count - 1):
            size = int(content_length * (carrier_percentages[i] / 100.0))
            size = min(size, remaining)  # Don't exceed remaining content
            chunk_sizes.append(size)
            remaining -= size
        
        # Last chunk gets all remaining content
        chunk_sizes.append(remaining)
        
        # Create chunks
        last_index = 0
        
        for i in range(carrier_count):
            size = chunk_sizes[i]
            
            # Get content slice
            content_slice = content[last_index:last_index + size] if i != carrier_count - 1 else content[last_index:]
            
            # Prepare chunk data
            chunk_data = {
                'chunk_id': i,
                'file_name': hidden_file.file_name if i == 0 else '',  # Only include filename in first chunk
                'content': content_slice,
                'is_last': (i == carrier_count - 1)
            }
            
            # Convert to string and add to chunks with delimiters
            chunk_str = str(chunk_data)
            delimited_chunk = f"####{chunk_str}####"
            content_chunks.append(delimited_chunk)
            last_index += size

        return content_chunks

    def process_content_chunks(self, content_chunks):
        # Sort chunks by their ID
        sorted_chunks = []
        file_name = "extracted_file.txt"  # Default filename
        
        for chunk in content_chunks:
            # Skip empty chunks
            if not chunk.strip():
                continue
                
            try:
                # Extract content between delimiters if they exist
                chunk = chunk.strip()
                if chunk.startswith('####') and chunk.endswith('####'):
                    chunk = chunk[4:-4]  # Remove delimiters
                
                # Parse the chunk data
                try:
                    chunk_data = eval(chunk)  # Be careful with eval in production!
                    if not isinstance(chunk_data, dict):
                        continue
                except:
                    continue
                
                # Get chunk data
                chunk_id = chunk_data.get('chunk_id')
                content = chunk_data.get('content', '')
                
                # Handle byte string representation if present
                if isinstance(content, str) and content.startswith("b'"):
                    try:
                        # Safely evaluate the string representation of bytes
                        content = eval(content)
                        if isinstance(content, bytes):
                            content = content.decode('utf-8', errors='replace')
                    except:
                        # If evaluation fails, clean up the string
                        if content.startswith("b'"):
                            content = content[2:-1]  # Remove b' and '
                        content = content.replace('\\n', '\n')  # Convert escaped newlines
                
                # Get filename from first chunk
                if chunk_id == 0 and 'file_name' in chunk_data:
                    file_name = chunk_data['file_name']
                
                sorted_chunks.append((chunk_id, str(content)))  # Ensure content is string
                
                # If this is the last chunk, we can stop processing
                if chunk_data.get('is_last', False):
                    break
                    
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue
        
        if not sorted_chunks:
            return None, None
            
        # Sort chunks by ID
        sorted_chunks.sort(key=lambda x: x[0])
        
        # Combine chunks
        full_content = "".join([content for _, content in sorted_chunks])
        
        return file_name, full_content

    def run(self, hidden_file_path: str, carrier_files_data: list[tuple[str, int]]):
        hidden_file = File(hidden_file_path)
        hidden_file.add_content(open(hidden_file_path, 'rb').read())

        carrier_files = []
        carrier_percentages = []
        for file_path, percentage in carrier_files_data:
            carrier_file = File(file_path)
            carrier_file.categorize()
            carrier_files.append(carrier_file)
            carrier_percentages.append(percentage)

        content_chunks = self.proccess_hidden_file(
            hidden_file, 
            carrier_files, 
            carrier_percentages=carrier_percentages
        )

        for i in range(len(carrier_files)):
            if carrier_files[i].category == "audio":
                audio_hider = Audio_Hider(carrier_files[i], content_chunks[i])
                audio_hider.hide_data()
            elif carrier_files[i].category == "image":
                image_hider = Image_Hider(carrier_files[i], content_chunks[i])
                image_hider.hide_data()
            elif carrier_files[i].category == "video":
                video_hider = Video_Hider(carrier_files[i], content_chunks[i])
                video_hider.hide_data()
            else:
                print(f"Unsupported file type: {carrier_files[i].category}")

    def extract(self, carrier_path):
        print(f"\n=== Starting extraction from: {carrier_path} ===")
        file_handler = File_Handeler(carrier_path)
        file_handler.load_files()
        
        print(f"Found {len(file_handler.files)} carrier files")
        if not file_handler.files:
            print("Error: No carrier files found in the specified directory")
            return

        content_chunks = []
        for i, file in enumerate(file_handler.files, 1):
            print(f"\nProcessing carrier file {i}/{len(file_handler.files)}: {file.file_path}")
            print(f"File type: {file.category}")
            try:
                chunk = None
                if file.category == "audio":
                    audio_hider = Audio_Hider(file, "")
                    print("Extracting from audio file...")
                    chunk = audio_hider.extract_data()
                    print(f"Raw audio chunk type: {type(chunk)}, length: {len(chunk) if chunk else 0}")
                    if chunk:
                        print(f"First 50 chars of audio chunk: {str(chunk)[:50]}")
                elif file.category == "image":
                    image_hider = Image_Hider(file, "")
                    print("Extracting from image file...")
                    chunk = image_hider.extract_data()
                    print(f"Raw image chunk type: {type(chunk)}, length: {len(chunk) if chunk else 0}")
                    if chunk:
                        print(f"First 50 chars of image chunk: {str(chunk)[:50]}")
                elif file.category == "video":
                    video_hider = Video_Hider(file, "")
                    print("Extracting from video file...")
                    chunk = video_hider.extract_data()
                    print(f"Raw video chunk type: {type(chunk)}, length: {len(chunk) if chunk else 0}")
                    if chunk:
                        print(f"First 50 chars of video chunk: {str(chunk)[:50]}")
                else:
                    print(f"Skipping unsupported file type: {file.category}")
                
                if chunk:
                    print(f"Successfully extracted chunk of length: {len(chunk)}")
                    content_chunks.append(chunk)
                else:
                    print("No data extracted from this file")
                    
            except Exception as e:
                print(f"Error extracting data from {file.file_path}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        print(f"\nExtraction complete. Found {len(content_chunks)} valid chunks.")
        
        if not content_chunks:
            print("Error: No valid data could be extracted from any carrier files")
            return

        print("\nProcessing content chunks...")
        print(f"Number of chunks to process: {len(content_chunks)}")
        for i, chunk in enumerate(content_chunks):
            print(f"Chunk {i} type: {type(chunk)}, length: {len(chunk) if chunk else 0}")
            if chunk:
                print(f"First 50 chars of chunk {i}: {str(chunk)[:50]}")
        
        file_name, extracted_content = self.process_content_chunks(content_chunks)
        
        if extracted_content is None:
            print("Error: Failed to process chunks - extracted content is None")
            return
            
        print(f"Successfully processed chunks. Extracted content length: {len(extracted_content)}")
        print(f"First 100 chars of extracted content: {str(extracted_content)[:100]}")
        
        print("\nCleaning extracted content...")
        cleaned_content = self.clean_mixed_output(extracted_content)
        
        if not cleaned_content:
            print("Error: No valid content after cleaning")
            return
            
        print(f"Cleaned content length: {len(cleaned_content)}")
        print(f"First 100 chars of cleaned content: {cleaned_content[:100]}")
        
        output_file_path = f"{self.output_path}{file_name}"
        print(f"\nSaving to: {output_file_path}")

        import os
        os.makedirs(self.output_path, exist_ok=True)

        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)
            print(f"\n=== Extraction successful! File saved to: {output_file_path} ===")
            return output_file_path
        except Exception as e:
            print(f"Error writing output file: {str(e)}")
            import traceback
            traceback.print_exc()

    def clean_mixed_output(self, raw: str) -> str:
        # If the input is already a string representation of bytes, clean it
        if isinstance(raw, str) and raw.startswith("b'"):
            try:
                # Safely evaluate the string representation of bytes
                raw = eval(raw)
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8', errors='replace')
            except:
                # If evaluation fails, clean up the string manually
                if raw.startswith("b'"):
                    raw = raw[2:-1]  # Remove b' and '
                raw = raw.replace('\\n', '\n')  # Convert escaped newlines
        
        # Clean up any remaining byte string markers or special characters
        if isinstance(raw, str):
            # Remove any remaining byte string markers
            raw = raw.replace("b'", "").replace("'", "")
            # Convert any remaining escaped characters
            raw = raw.encode().decode('unicode_escape')
            # Split into lines and preserve empty lines
            lines = raw.splitlines()
            # Clean up each line while preserving empty lines
            cleaned_lines = []
            for line in lines:
                if line.strip() == '':  # Preserve empty lines
                    cleaned_lines.append('')
                else:
                    cleaned_lines.append(line.strip())
            # Join lines back together with newlines
            return '\n'.join(cleaned_lines)
        
        return str(raw)

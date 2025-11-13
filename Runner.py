from objects.File import File
from Audio_Hider import Audio_Hider
from Image_Hider import Image_Hider
from Video_Hider import Video_Hider
from File_Handeler import File_Handeler

import ast
import random

class Runner:
    def __init__(self):
        self.output_path = "output_files/"

    def proccess_hidden_file(self, hidden_file, carrier_files):
        content = [c for c in str(hidden_file.file_content)]
        carrier_count = len(carrier_files)
        
        print(f"content: {content}")
        print(f"raw content: {hidden_file.file_content}")

        key = []
        seed = random.randint(1, 10000)
        random.seed(seed)
        for i in range(len(content)):
            key.append(random.randint(0, 1))

        temp_content0 = content[0:int(len(content)/2)]
        temp_content1 = content[int(len(content)/2):]

        temp_content1.reverse()

        print(f"temp_content0: {temp_content0}")
        print(f"temp_content1: {temp_content1}")
        print(f"key: {key}")

        processed_content = []

        for i in range(len(key) - 1):
            if len(temp_content0) > 0:
                if len(temp_content1) > 0:
                    if key[i] == 0:
                        processed_content.extend([temp_content0.pop(0)])
                    else:
                        processed_content.extend([temp_content1.pop(0)])
                else:
                    processed_content.append(temp_content0[0:])
                    break
            else:
                processed_content.extend(temp_content1[0:])
                break

        print(f"processed_content: {processed_content}")

        content_chunks = []

        last_index = 0
        for i in range(carrier_count):
            print(f"Processing carrier {i}: carrier_files[{i}][1] = {carrier_files[i][1]}")
            percent = carrier_files[i][1] / 100.0
            size = int(len(processed_content) * percent)
            print(f"  percent={percent}, size={size}")

            chunk = ""

            if i == 0:
                chunk += f"#-0-{seed}-{hidden_file.file_name}-#"
                chunk += "".join(str(c) for c in processed_content[:size])
            elif i == carrier_count - 1:
                chunk += f"#-{i}-end-#"
                chunk += "".join(str(c) for c in processed_content[last_index:])
            else:
                chunk += f"#-{i}-#"
                chunk += "".join(str(c) for c in processed_content[last_index:last_index + size])
            
            last_index += size
            content_chunks.append(chunk)
        
        print(f"content_chunks: {content_chunks}")

        return content_chunks

    def process_content_chunks(self, content_chunks):
        print(f"content_chunks: {content_chunks}")
        sorted_chunks = []
        for chunk in content_chunks:
            print(f"Processing chunk: {chunk}")
            print(f"chunk.split('-'): {chunk.split('-')}")
            chunk_id = chunk.split("-")[1]  
            sorted_chunks.insert(int(chunk_id), chunk)
        
        print(f"sorted_chunks: {sorted_chunks}")
        
        seed = int(sorted_chunks[0].split("-")[2]) 
        file_name = sorted_chunks[0].split("-")[3] 
        
        print(f"seed: {seed}")
        print(f"file_name: {file_name}")
        
        processed_content = ""
        for chunk in sorted_chunks:
            content_part = chunk[chunk.index("-#") + 2:]
            processed_content += content_part
        


        print(f"processed_content: {processed_content}")

        total_size = len(processed_content)

        key = []
        random.seed(seed)
        for i in range(total_size):
            key.append(random.randint(0, 1))

        print(f"key: {key}")

        temp_content0 = []
        temp_content1 = []

        for i in range(len(key) - 1):
            if len(temp_content0) < int(total_size/2):
                if len(temp_content1) < int(total_size/2):
                    if key[i] == 0:
                        temp_content0.append(processed_content[i])
                    else:
                        temp_content1.append(processed_content[i])
                else:
                    temp_content0.append(processed_content[i])
                    break
            else:
                temp_content1.append(processed_content[i])
                break

        print(f"temp_content0: {temp_content0}")
        print(f"temp_content1: {temp_content1}")

        temp_content1.reverse()

        final_content = "".join(temp_content0) + "".join(temp_content1)



        print(f"final_content: {final_content}")

        return file_name, final_content

    def run(self, hidden_file_path: str, carrier_files_data: list[tuple[str, int]]):
        hidden_file = File(hidden_file_path)
        hidden_file.add_content(open(hidden_file_path, 'rb').read())

        carrier_files = []

        for file_path, percentage in carrier_files_data:
            carrier_file = File(file_path)
            carrier_file.categorize()
            carrier_files.append(carrier_file)
        
        content_chunks = self.proccess_hidden_file(hidden_file, carrier_files_data)

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
        file_handler = File_Handeler(carrier_path)
        file_handler.load_files()

        content_chunks = []
        for file in file_handler.files:
            if file.category == "audio":
                audio_hider = Audio_Hider(file, "")
                content_chunks.append(audio_hider.extract_data())
            elif file.category == "image":
                image_hider = Image_Hider(file, "")
                content_chunks.append(image_hider.extract_data())
            elif file.category == "video":
                video_hider = Video_Hider(file, "")
                content_chunks.append(video_hider.extract_data())
        
        file_name, extracted_content = self.process_content_chunks(content_chunks)

        cleaned_content = self.clean_mixed_output(extracted_content)
        
        output_file_path = f"{self.output_path}{file_name}"

        import os
        os.makedirs(self.output_path, exist_ok=True)
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)

    def clean_mixed_output(self, raw: str) -> str:
        parts = [p.strip() for p in raw.split(',')]
        cleaned = []
        for p in parts:
            if not p:
                continue
            try:
                val = ast.literal_eval(p)
                if isinstance(val, bytes):
                    val = val.decode('utf-8', errors='ignore')
                cleaned.append(str(val))
            except Exception:
                cleaned.append(p)
        joined = '\n'.join(cleaned)
        return joined.encode('utf-8', 'ignore').decode('unicode_escape')

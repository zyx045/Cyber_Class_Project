import os
 
from objects.File import File

class File_Handeler:
    def __init__(self, source_path):
        self.source_path = source_path
        self.files = []


    def create_file_object(self, file_path):
        file = File(file_path)
        
        content = []
        with open(file_path, "rb") as f:
            content = f.read()
        
        file.add_content(content)
        return file

    def load_files(self):
        for file_path in os.listdir(self.source_path):
            self.files.append(self.create_file_object(self.source_path + "/" + file_path))
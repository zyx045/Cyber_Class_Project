import os

class File:
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            print("File does not exist: path: " + file_path)
            raise FileNotFoundError("File does not exist")
        self.file_path = file_path
        self.file_name = file_path.split("/")[-1]
        self.file_extension = file_path.split(".")[-1]
        self.file_size = os.path.getsize(file_path)
        self.file_content = None
        self.category = None
        self.categorize()

    def add_content(self, content):
        self.file_content = content

    def categorize(self):
        if self.file_extension in ["png", "jpg", "jpeg", "gif"]:
            self.category = "image"
        elif self.file_extension in ["mp3", "wav"]:
            self.category = "audio"
        elif self.file_extension in ["mp4", "gif"]:
            self.category = "video"
        else:
            self.category = "other"
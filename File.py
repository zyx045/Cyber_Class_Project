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
        """Categorize the file based on its extension.
        
        Categories:
            - image: Common image formats
            - audio: Supported audio formats (including lossless and lossy)
            - video: Common video formats
            - other: Any other file type
        """
        # Case-insensitive extension check
        ext = self.file_extension.lower()
        
        # Define supported formats
        image_exts = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"}
        audio_exts = {
            # Lossless formats
            "wav", "flac", "alac", "aif", "aiff", "dsf", "pcm",
            # Lossy formats
            "mp3", "aac", "m4a", "ogg", "opus"
        }
        video_exts = {"mp4", "avi", "mov", "mkv", "flv", "webm", "wmv", "m4v"}
        
        # Categorize the file
        if ext in image_exts:
            self.category = "image"
        elif ext in audio_exts:
            self.category = "audio"
        elif ext in video_exts:
            self.category = "video"
        else:
            self.category = "other"
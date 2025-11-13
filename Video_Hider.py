from mutagen.mp4 import MP4
import os


class Video_Hider:
    HIDDEN_TAG = "©msg"  # Custom metadata key (not displayed by players)

    def __init__(self, host_file, hidden_data):
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.output_path = "output_files/"

    def hide_data(self):
        # Copy input file to output first
        with open(self.host_file.file_path, "rb") as src, open(self.output_path + self.host_file.file_name.split('.')[0] + "_stego.mp4", "wb") as dst:
            dst.write(src.read())

        video = MP4(self.output_path + self.host_file.file_name.split('.')[0] + "_stego.mp4")
        video[self.HIDDEN_TAG] = [self.hidden_data]
        video.save()


    def extract_data(self) -> str:
        video = MP4(self.host_file.file_path)

        if self.HIDDEN_TAG in video.tags:
            return video[self.HIDDEN_TAG][0]
        else:
            return "(No hidden message found)"


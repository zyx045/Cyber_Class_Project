import os
import wave
from pydub import AudioSegment


class Audio_Hider:
    def __init__(self, host_file, hidden_data):
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.temp_path = "temp_files/"
        self.output_path = "output_files/"
        self.end_marker = "#END_OF_MESSAGE#"

    def covert_data_to_binary(self, text: str) -> str:
        return ''.join(format(ord(c), '08b') for c in text) + ''.join(format(ord(c), '08b') for c in self.end_marker)

    def convert_binary_to_data(self, bits: str) -> str:
        chars = [bits[i:i + 8] for i in range(0, len(bits), 8)]
        return ''.join(chr(int(b, 2)) for b in chars)

    def _encode_wav(self, file_path, output_path):
        bits = self.covert_data_to_binary(self.hidden_data)

        with wave.open(file_path, 'rb') as audio:
            params = audio.getparams()
            frames = bytearray(list(audio.readframes(audio.getnframes())))

        for i, bit in enumerate(bits):
            frames[i] = (frames[i] & 254) | int(bit)

        with wave.open(output_path, 'wb') as out_audio:
            out_audio.setparams(params)
            out_audio.writeframes(bytes(frames))

    def _decode_wav(self, stego_wav: str) -> str:
        with wave.open(stego_wav, 'rb') as audio:
            frames = bytearray(list(audio.readframes(audio.getnframes())))

        extracted_bits = ''.join([str(frame & 1) for frame in frames])
        decoded = self.convert_binary_to_data(extracted_bits)

        end_index = decoded.find(self.end_marker)
        if end_index != -1:
            decoded = decoded[:end_index]

        return decoded


    def hide_data(self):
        temp_input_wav = self.temp_path + "temp_input.wav"
        temp_output_wav = self.temp_path + "temp_output.wav"

        if self.host_file.file_extension == "mp3":
            AudioSegment.from_mp3(self.host_file.file_path).export(temp_input_wav, format="wav")
        else:
            temp_input_wav = self.host_file.file_path

        self._encode_wav(temp_input_wav, temp_output_wav)

        #if self.host_file.file_extension == "mp3":
        #   AudioSegment.from_wav(temp_output_wav).export(self.output_path + self.host_file.file_name.split('.')[0] + ".mp3", format="mp3")
        #else:
        os.replace(temp_output_wav, self.output_path + self.host_file.file_name.split('.')[0] + ".wav")

        for f in ["temp_input.wav", "temp_output.wav"]:
            if os.path.exists(self.temp_path + f):
                os.remove(self.temp_path + f)


    def extract_data(self) -> str:
        os.makedirs(self.temp_path, exist_ok=True)
        temp_wav = os.path.join(self.temp_path, "temp_decode.wav")
        used_temp = False

        if self.host_file.file_extension.lower() == "mp3":
            AudioSegment.from_mp3(self.host_file.file_path).export(temp_wav, format="wav")
            used_temp = True
        else:
            temp_wav = self.host_file.file_path  

        
        message = self._decode_wav(temp_wav)
        print(f"Extracted message: {message}")

        
        if used_temp and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except PermissionError:
                pass  

        return message
import os
from PIL import Image

class Image_Hider:
    def __init__(self, host_file, hidden_data):
        self.host_file = host_file
        self.hidden_data = hidden_data
        self.output_path = "output_files/"
        self.working_image = self.load_image()

    def convert_data_to_binary(self):
        """Convert message text into a list of 8-bit binary strings."""
        return [format(ord(i), '08b') for i in self.hidden_data]

    def load_image(self):
        """Load and copy the host image directly (no temp file)."""
        os.makedirs(self.output_path, exist_ok=True)
        image = Image.open(self.host_file.file_path)
        working_image = image.copy() 
        return working_image

    def output_image(self):
        """Save the steganographic image."""
        output_file_path = os.path.join(self.output_path, self.host_file.file_name)
        self.working_image.save(output_file_path)
        return output_file_path

    def modify_pixel(self, pix):
        """Yield modified pixel tuples embedding message bits."""
        datalist = self.convert_data_to_binary()
        lendata = len(datalist)
        imdata = iter(pix)
    
        for i in range(lendata):
            pixels = [value for value in next(imdata)[:3] +
                      next(imdata)[:3] +
                      next(imdata)[:3]]
        
            for j in range(8):
                if datalist[i][j] == '0' and pixels[j] % 2 != 0:
                    pixels[j] -= 1
                elif datalist[i][j] == '1' and pixels[j] % 2 == 0:
                    pixels[j] = pixels[j] - 1 if pixels[j] != 0 else pixels[j] + 1
        
            if i == lendata - 1:
                pixels[-1] |= 1
            else:
                pixels[-1] &= ~1
        
            yield tuple(pixels[:3])
            yield tuple(pixels[3:6])
            yield tuple(pixels[6:9])

    def hide_data(self):
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

        self.output_image()

    def extract_data(self):
        imgdata = iter(self.working_image.getdata())
        data = ""
    
        while True:
            try:
                pixels = [value for value in next(imgdata)[:3] +
                          next(imgdata)[:3] +
                          next(imgdata)[:3]]
            except StopIteration:
                break

            binstr = ''.join(['1' if i % 2 else '0' for i in pixels[:8]])
            data += chr(int(binstr, 2))
        
            if pixels[-1] % 2 != 0:
                break
    
        return data

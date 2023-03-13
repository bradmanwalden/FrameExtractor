import json
import ffmpeg
import srt
import re
from datetime import timedelta
from exif import Image

from tkinter import filedialog
import tkinter as tk
from tkinter import ttk


altitude_modes = {
    'Absolute': 'abs',
    'Relative': 'rel',
    'Ignore': "none"
}

def DD_to_DMS(deg):
    """
    Convert decimal degrees to degrees, minutes, seconds.
    
    params:
        deg: float, degrees in decimal format
    returns: tuple, (degrees, minutes, seconds)
    """

    m, s = divmod(abs(deg)*3600, 60)
    d, m = divmod(m, 60)
    if deg < 0:
        d = -d
    #d, m = int(d), int(m)
    s = round(s, 4)
    return (d, m, s)

# Extract images from video
def extractImages(videoPath, srtPath, outputPath, nthFrame, name, altitude_mode, fps):
    """
    Extract images from video at specified intervals and write GPS data to images.
    
    params:
        videoPath: str, path to video file
        srtPath: str, path to srt file
        outputPath: str, path to output folder
        nthFrame: int, extract image every nth frame
        name: str, prefix for image names
        altitude_mode: str, 'abs' for absolute altitude, 'rel' for relative altitude, 'none' for no altitude
        fps: int, frames per second of video
        
    returns: None
    """
    global root
    root.destroy()
    if name != "":
        name = name + "_"
    # Open srt file
    with open(srtPath, 'r') as f:
        subs = srt.parse(f.read())

    # Open video file
    vid = ffmpeg.input(videoPath)
    j = 0


    
    for i, sub in enumerate(subs):
        if i % nthFrame == 0:
            j += 1
            # extract image at time
            print(sub.start.total_seconds())
            filename = "{}/{}{}.JPG".format(outputPath, name, j)
            (
                vid
                .filter('select', f'eq(n,{i})')
                .output(filename, vframes=1)
                .run()
            )
            
            # get data
            #try:
            if True:
                print(sub.content)
                time = re.search(r'(\d\d\d\d-\d+-\d+ \d+:\d+:\d+)', sub.content).group(1)
                print(time)
                lat = float(re.search(r'latitude *: *(-?\d+\.\d+)', sub.content).group(1))
                print(lat)
                lon = float(re.search(r'longitude *: *(-?\d+\.\d+)', sub.content).group(1))
                print(lon)
                if altitude_mode == 'rel':
                    alt = float(re.search(r'rel_alt *: *(-?\d+\.\d+)', sub.content).group(1))
                if altitude_mode == 'abs':
                    alt = float(re.search(r'abs_alt *: *(-?\d+\.\d+)', sub.content).group(1))
                
            #except:
                #print("Error: Could not find coordinates in subtitle for frame at time {}".format(sub.start))
                #continue
            #else:
                

                # write data to image
                with open(filename, 'rb') as image_file:
                    my_image = Image(image_file)
                
                if lat < 0:
                    my_image.gps_latitude_ref = 'S'
                    lat = -lat
                else:
                    my_image.gps_latitude_ref = 'N'
                
                if lon < 0:
                    my_image.gps_longitude_ref = 'W'
                    lon = -lon
                else:
                    my_image.gps_longitude_ref = 'E'
                lat = DD_to_DMS(lat)
                lon = DD_to_DMS(lon)

                my_image.datetime = time
                my_image.gps_latitude = lat
                my_image.gps_longitude = lon
                if altitude_mode != 'none':
                    my_image.gps_altitude = alt
                
                with open(filename, 'wb') as new_image_file:
                    new_image_file.write(my_image.get_file())
                    

def start(videoPath, srtPath, outputPath):
    global root
    #get frames per second
    vid = ffmpeg.probe(videoPath)
    fps = vid['streams'][0]['r_frame_rate']
    fps = int(fps.split('/')[0]) / int(fps.split('/')[1])
    print(json.dumps(vid, indent=4))
    fps = int(round(fps,0))

    totalFrames = int(vid['streams'][0]['nb_frames'])
    totalSeconds = int(round(float(vid['streams'][0]['duration']), 0))

    # Tkinter GUI
    root = tk.Tk()
    root.title("Extract Images")

    nameLabel = tk.Label(root, text="Name Prefix", font=("Helvetica", 20))
    nameLabel.grid(row=0, column=0, sticky=tk.E)

    nameEntry = tk.Entry(root)
    nameEntry.grid(row=0, column=1, sticky=tk.W)

    nameHelp = tk.Label(root, text="This will be the prefix of the image names. Leave blank for no prefix.")
    nameHelp.grid(row=1, column=0, columnspan=2)

    nthFrameLabel = tk.Label(root, text="Frame Interval", font=("Helvetica", 20))
    nthFrameLabel.grid(row=2, column=0, sticky=tk.E)

    nthFrameScale = tk.Scale(root, from_=1, to=300, orient=tk.HORIZONTAL, length=200, tickinterval=10)
    nthFrameScale.set(fps)
    nthFrameScale.grid(row=2, column=1, sticky=tk.W)

    nthFrameHelp = tk.Label(root, text=f"Your file is {fps} fps, with a total of {totalFrames}, lasting {totalSeconds} secs.\nA value of 1 will extract every frame, a value of 2 will extract every other frame, etc.\nA value of {fps} will extract one frame per second.")
    nthFrameHelp.grid(row=3, column=0, columnspan=2)

    altitudeModeLabel = tk.Label(root, text="Altitude mode", font=("Helvetica", 20))
    altitudeModeLabel.grid(row=4, column=0, sticky=tk.E)

    altitudeModeMenu = ttk.Combobox(root, values=list(altitude_modes.keys()))
    altitudeModeMenu.current(0)
    altitudeModeMenu.grid(row=4, column=1, sticky=tk.W)

    altitudeModeHelp = tk.Label(root, text="Choose whether to use relative or absolute altitude. If you don't know what this means, leave it at 'Absolute'.")
    altitudeModeHelp.grid(row=5, column=0, columnspan=2)

    submitButton = tk.Button(root, text="Submit", command=lambda: extractImages(videoPath, srtPath, outputPath, nthFrameScale.get(), nameEntry.get(), altitude_modes[altitudeModeMenu.get()], fps), font=("Helvetica", 20))

    submitButton.grid(row=6, column=0, columnspan=2)

    creditLabel = tk.Label(root, text="Made by Bradley Walden (www.bradleywalden.site)")
    creditLabel.grid(row=7, column=0, columnspan=2)
    root.mainloop()




if __name__ == "__main__":
    videoPath = filedialog.askopenfilename(title="Select video file", filetypes=(("Video Files","*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.m4v *.mpg"), ("All files", "*.*")))
    srtPath = filedialog.askopenfilename(title="Select srt file", filetypes=(("SRT files", "*.SRT"), ("All files", "*.*")))
    outputPath = filedialog.askdirectory(title="Select output folder")
    start(videoPath, srtPath, outputPath)

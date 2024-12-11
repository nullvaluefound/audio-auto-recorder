import os
from os import environ
from collections import deque
import pyaudiowpatch as pyaudio
import threading
import wave
import datetime
from pynput.keyboard import Key, Listener

DURATION = 300.0
CHUNK_SIZE = 2048
global FRAMES
global CHANNELS
global FRAME_RATE
global folderpath
folderpath = environ.get('HOMEDRIVE') + environ.get('HOMEPATH') + "\\Videos\\Loopback\\"
try:
    os.listdir(folderpath)
except FileNotFoundError as e:
    os.mkdir(folderpath)

def record_continually():
    global FRAMES
    global CHANNELS
    global FRAME_RATE
    FRAMES = deque([])


    with pyaudio.PyAudio() as p:
        """
        Create PyAudio instance via context manager.
        Spinner is a helper class, for `pretty` output
        """
        try:
            # Get default WASAPI info
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("Looks like WASAPI is not available on the system. Exiting...")
            exit()

        # Get default WASAPI speakers
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                """
                Try to find loopback device with same name(and [Loopback suffix]).
                Unfortunately, this is the most adequate way at the moment.
                """
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                print(
                    "Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices.\nExiting...\n")
                exit()

        print(f"Recording from: ({default_speakers['index']}){default_speakers['name']}")

        CHANNELS = default_speakers["maxInputChannels"]
        FRAME_RATE = int(default_speakers["defaultSampleRate"])

        with p.open(format=pyaudio.paInt16,
                    channels=default_speakers["maxInputChannels"],
                    rate=int(default_speakers["defaultSampleRate"]),
                    frames_per_buffer=CHUNK_SIZE,
                    input=True,
                    input_device_index=default_speakers["index"],
                    ) as stream:

            frame_idx = int((default_speakers["defaultSampleRate"] / CHUNK_SIZE) * DURATION)
            print(frame_idx)
            while True:
                if len(FRAMES) < frame_idx:
                    FRAMES.append(stream.read(CHUNK_SIZE))
                else:
                    FRAMES.popleft()
                    FRAMES.append(stream.read(CHUNK_SIZE))


def save():
    filename = f"{str(datetime.datetime.now()).replace(':', '_').replace(' ', '-').split('.')[0]}.wav"
    fullpath = folderpath+filename
    print(len(FRAMES))
    wave_file = wave.open(fullpath, 'wb')
    wave_file.setnchannels(CHANNELS)
    wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(FRAME_RATE)
    wave_file.writeframesraw(b''.join(FRAMES))
    wave_file.close()

def on_press(key):
    if key == Key.scroll_lock:
        print("Key Pressed")
        save()


if __name__ == "__main__":
    # Create a keyboard listener
    with Listener(on_press=on_press) as listener:
        # Start listening for keystrokes
        aud_listening = threading.Thread(target=record_continually)
        aud_listening.start()
        listener.join()






import os
import pathlib
import shutil

import cv2
import numpy as np
from math import ceil
from sys import argv
import subprocess


def remove_directory_content(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def directory_exists(directory):
    return os.path.exists(directory)


def make_dir(directory):
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)


def required_frame_count(video_capture, image):
    vid_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    vid_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)

    img_height = image.shape[0]
    img_width = image.shape[1]

    # header length is 64
    return int(ceil((img_height * img_width * 8 + 64) / (vid_height * vid_width)))


def bin_rep(num):
    return "{0:b}".format(num)


# creates stegano video
def hide(carrier_video, image_message):
    cap = cv2.VideoCapture(carrier_video)
    msg = cv2.imread(image_message)

    vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_fps = cap.get(cv2.CAP_PROP_FPS)

    req_frame_count = required_frame_count(cap, msg)

    bin_rep_width = bin_rep(msg.shape[1]).zfill(16)

    bin_rep_height = bin_rep(msg.shape[0]).zfill(16)

    bin_rep_mult = bin_rep(msg.shape[0] * msg.shape[1]).zfill(32)

    image_bits = [int(x == '1') for x in bin_rep_width + bin_rep_height + bin_rep_mult]

    for row in msg:
        for column in row:
            for color in column:
                for i in range(8):
                    image_bits.append(int((color & (1 << (7 - i))) != 0))

    video_colors = []

    for i in range(req_frame_count):
        ret, frame = cap.read()
        if not ret:
            raise Exception('Error in extracting video frames')

        for row in frame:
            for column in row:
                for color in range(3):
                    video_colors.append(column[color])

    assert len(video_colors) >= len(image_bits)
    for i in range(len(video_colors) - len(image_bits)):
        image_bits.append(0)

    video_colors = [(color & 0xFE) for color in video_colors]

    for i in range(len(video_colors)):
        video_colors[i] |= image_bits[i]

    video_colors = np.reshape(np.asarray(video_colors), (req_frame_count, vid_height, vid_width, 3)).astype(np.uint8)

    # create dirs
    if os.path.exists("temp"):
        remove_directory_content("temp")
    else:
        make_dir("temp")

    cnt = 1

    for frame in video_colors:
        cv2.imwrite('./temp/frame{:09d}.png'.format(cnt), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        cnt += 1

    print('Starting write back...')
    while True:
        ret, frame = cap.read()

        if ret:
            cv2.imwrite('./temp/frame{:09d}.png'.format(cnt), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            cnt += 1
        else:
            break

    subprocess.call(
        ["ffmpeg", "-y", "-framerate", str(vid_fps), "-i", "./temp/frame%09d.png", "-c:v", "copy", "stegano.mp4"])
    cap.release()
    print('Done. Stegano video created (stegano.mp4)')
    remove_directory_content("temp")


def bool2int(x):
    x = x[::-1]
    y = 0
    for i, j in enumerate(x):
        y += j << i
    return y


def extract(stegano_video):
    if os.path.exists("temp_out"):
        remove_directory_content("temp_out")
    else:
        make_dir("temp_out")

    subprocess.call(["ffmpeg", "-y", "-i", stegano_video, "./temp_out/frame%09d.png"])

    frame_index = 1

    message_length = None
    message_width = None
    message_height = None
    frame_width = None
    frame_height = None

    message_bits = []

    while True:
        frame_path = "./temp_out/frame{:09d}.png".format(frame_index)
        if not os.path.exists(frame_path):
            break

        frame = cv2.imread(frame_path)

        for row in frame:
            for column in row:
                for color in column:
                    message_bits.append((color & 1) == 1)

        if frame_index == 1:
            frame_bits = message_bits

            width = bool2int(frame_bits[:16])
            height = bool2int(frame_bits[16:32])
            mult = bool2int(frame_bits[32:64])

            if height * width != mult:
                raise Exception("Invalid stegano video, no valid message was found in {}".format(stegano_video))
            message_length = mult * 8 * 3 + 64
            frame_height = frame.shape[0]
            frame_width = frame.shape[1]
            message_height = height
            message_width = width
        else:
            if (frame_width * frame_height * frame_index) > message_length:
                break

        frame_index += 1

    print("Extracting...")
    message_bytes = np.asarray(message_bits[64:message_length]).reshape((-1, 8))
    message_bytes = [bool2int(x) for x in message_bytes]
    message = np.asarray(message_bytes).reshape((message_height, message_width, 3))
    print('Done. Hidden message was saved to extracted.png')
    remove_directory_content("temp_out")
    cv2.imwrite('extracted.png', message, [cv2.IMWRITE_PNG_COMPRESSION, 0])


mode = argv[1]

if mode == '-hide':
    if len(argv) < 4:
        raise Exception("No arguments were given for carrier video path and message image path")
    carrier_video_path = argv[2]
    image_message_path = argv[3]
    if not os.path.exists(carrier_video_path):
        raise Exception("Carrier video {} was not found".format(carrier_video_path))
    if not os.path.exists(image_message_path):
        raise Exception("Image message {} was not found".format(carrier_video_path))

    hide(carrier_video_path, image_message_path)
elif mode == '-extract':
    if (len(argv) < 3):
        raise Exception("No argument was given for stegano video")
    stegano_video_path = argv[2]
    if not os.path.exists(stegano_video_path):
        raise Exception("Stegano video {} was not found".format(stegano_video_path))
    extract(stegano_video_path)
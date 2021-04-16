import os
import pathlib
import shutil

import cv2
import numpy as np
from math import ceil
from sys import argv
import skvideo.io
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

def directory_exists(dir):
    return os.path.exists(dir)

def make_dir(dir):
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)

def required_frame_count(video_capture, image):
    vid_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    vid_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)

    img_height = image.shape[0]
    img_width = image.shape[1]

    # header length is 32
    return int(ceil((img_height * img_width * 8 + 32) / (vid_height * vid_width)))


def bin_rep(num):
    return "{0:b}".format(num)


# creates stegano video
def hide(carrier_video, image_message, stegano_video='Output/stegano.mp4'):
    cap = cv2.VideoCapture(carrier_video)
    msg = cv2.imread(image_message)

    vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_fps = cap.get(cv2.CAP_PROP_FPS)

    req_frame_count = required_frame_count(cap, msg)

    outputfile = "test.mp4"  # our output filename
    writer = skvideo.io.FFmpegWriter(outputfile, outputdict={
        '-vcodec': 'libx264',  # use the h.264 codec
        '-crf': '0',  # set the constant rate factor to 0, which is lossless
        '-preset': 'veryslow'  # the slower the better compression, in princple, try
        # other options see https://trac.ffmpeg.org/wiki/Encode/H.264
    })
    image_bits = []
    bin_rep_width = bin_rep(msg.shape[1])
    bin_rep_width = '0' * (16 - len(bin_rep_width)) + bin_rep_width

    bin_rep_height = bin_rep(msg.shape[0])
    bin_rep_height = '0' * (16 - len(bin_rep_height)) + bin_rep_height

    print('height is {}'.format(msg.shape[0]))
    print('width is {}'.format(bin_rep_width))
    print('height is {}'.format(bin_rep_height))

    image_bits += [int(x == '1') for x in bin_rep_width + bin_rep_height]

    print('image bits is {}'.format(image_bits))
    print(req_frame_count)

    for row in msg:
        for column in row:
            for color in column:
                for i in range(8):
                    image_bits.append(int((color & (1 << (7 - i))) != 0))

    print('len of image_bits is {}'.format(len(image_bits)))

    video_colors = []

    ff = []

    for i in range(req_frame_count):
        ret, frame = cap.read()
        if (ret == False):
            raise Exception('Fucked')
        print(frame.shape)
        ff.append(frame)
        for row in frame:
            for column in row:
                for i in range(3):
                    video_colors.append(column[i])

    assert len(video_colors) >= len(image_bits)
    for i in range(len(video_colors) - len(image_bits)):
        image_bits.append(0)

    print('vc is {}'.format(video_colors[:32]))

    video_colors = [(color & 0xFE) for color in video_colors]

    print('vc is {}'.format(video_colors[:32]))

    print('image_bits is {}'.format(image_bits[:40]))

    for i in range(len(video_colors)):
        video_colors[i] |= image_bits[i]

    print('vc is {}'.format(video_colors[:32]))

    video_colors = np.reshape(np.asarray(video_colors), (req_frame_count, vid_height, vid_width, 3)).astype(np.uint8)

    # create dirs
    if (os.path.exists("temp")):
        remove_directory_content("temp")
    else:
        make_dir("temp")

    cnt = 1

    for frame in video_colors:
        x = frame[:, :, ::-1]
        cv2.imwrite('./temp/frame{:09d}.png'.format(cnt), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        # writer.writeFrame(x)
        cnt += 1

    print('start write back')
    while (True):
        ret, frame = cap.read()

        if (ret):
            # writer.writeFrame(frame[:,:,::-1])
            cv2.imwrite('./temp/frame{:09d}.png'.format(cnt), frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
            cnt += 1
        else:
            break

    subprocess.call(
        ["ffmpeg", "-y", "-framerate", str(vid_fps), "-i", "./temp/frame%09d.png", "-c:v", "copy", "out.mp4"])
    cap.release()


def extract(stegano_video):
    if (os.path.exists("temp_out")):
        print("Hi")
        remove_directory_content("temp_out")
    else:
        make_dir("temp_out")

    subprocess.call(["ffmpeg", "-y", "-i", stegano_video, "./temp_out/frame%09d.png"])

    frame_index = 1

    while True:
        frame_path = "./temp_out/frame{:09d}.png".format(frame_index)
        if (not os.path.exists(frame_path)):
            break

        frame = cv2.imread(frame_path)

        if (frame_index == 1):
            frame_bytes = []
            width = ""
            height = ""

            for row in frame:
                for column in row:
                    for color in column:
                        frame_bytes.append(color)

            print("frame_bytes: {}".format(frame_bytes[:32]))

            for i in range(16):
                width += (chr(ord('0') + int((frame_bytes[i] & 1) != 0)))
                height += (chr(ord('0') + int((frame_bytes[i + 16] & 1) != 0)))

            print(height, width)
            width = int('0b' + width, 2)
            height = int('0b' + height, 2)
            print(height, width)
            print()
            print(frame)
            break

#    cap = cv2.VideoCapture(stegano_video)
#    for i in range(100):
#        frame_bytes = []
#        ret, first_frame = cap.read()
#        print('first frame is {}'.format(first_frame))
#        print('ret was {}'.format(ret))
#
#    while True:
#        ret, frame = cap.read()
#
#        if (not ret):
#            break
#
#        for row in frame:
#            for column in row:
#                for color in column:
#                    frame_bytes.append(color)
#
#        print('frame was {}'.format(frame))
#
#    width = ""
#    height = ""
#
#    for i in range(16):
#        width += (chr(ord('0') + int((frame_bytes[i] & 1) != 0)))
#        height += (chr(ord('0') + int((frame_bytes[i + 16] & 1) != 0)))
#
#    print(width, height)
#    width = int('0b' + width, 2)
#    height = int('0b' + height, 2)
#
#    print(width, height)
#    cap.release()

mode = argv[1]

if (mode == '-hide'):
    carrier_video_path = argv[2]
    image_message_path = argv[3]
    hide(carrier_video_path, image_message_path)
elif (mode == '-extract'):
    stegano_video_path = argv[2]
    extract(stegano_video_path)

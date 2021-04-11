import cv2
import numpy as np
from math import ceil
from sys import argv

def required_frame_count(video_capture, image):
    vid_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    vid_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)

    img_height = image.shape[0]
    img_width = image.shape[1]

    # header length is 32
    return int(ceil((img_height * img_width * 8 + 32) / (vid_height * vid_width)))

# creates stegano video
def hide(carrier_video, image_message, stegano_video = 'Output/stegano.mp4'):
    cap = cv2.VideoCapture(carrier_video)
    msg = cv2.imread(image_message)

    vid_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_fps = cap.get(cv2.CAP_PROP_FPS)

    req_frame_count = required_frame_count(cap, msg)

    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    out = cv2.VideoWriter('output.mp4', fourcc, vid_fps, (vid_width, vid_height))

    image_bits = []

    print(req_frame_count)

    for row in msg:
        for column in row:
            for color in column:
                for i in range(8):
                    image_bits.append(int(color & (1 << i) != 0))

    print('len of image_bits is {}'.format(len(image_bits)))

    video_colors = []

    for i in range(req_frame_count):
        ret, frame = cap.read()
        if (ret == False):
            raise Exception('Fucked')
        print(frame.shape)
        for row in frame:
            for column in row:
                for i in range(3):
                    video_colors.append(column[i])

    assert len(video_colors) >= len(image_bits)
    for i in range(len(video_colors) - len(image_bits)):
        image_bits.append(0)

    video_colors = [(color & 0xFFFFF0) for color in video_colors]
    for i in range(len(video_colors)):
        video_colors[i] |= image_bits[i]

    video_colors = np.asarray(video_colors).reshape(req_frame_count, vid_width, vid_height, 3)

    for frame in video_colors:
        out.write(frame)

    print('start write back')
    cnt = 0
    while (True):
        ret, frame = cap.read()

        if (ret):
            cnt += 1
            out.write(frame)
        else:
            break
    print('cnt is {}'.format(cnt))
    cap.release()
    out.release()

def extract(stegano_video):
    pass

mode = argv[1]

if (mode == '-hide'):
    carrier_video_path = argv[2]
    image_message_path = argv[3]
    hide(carrier_video_path, image_message_path)
elif (mode == '-extract'):
    try:
        stegano_video_path = argv[2]
        extract(stegano_video_path)
    except Exception as e:
        print('Invalid arguments', e)


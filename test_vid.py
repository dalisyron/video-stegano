import cv2
from math import ceil
from sys import argv

trailer = '1010100001001001010'

def required_frame_count(video_capture, image):
    vid_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    vid_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)

    img_height = image.shape[0]
    img_width = image.shape[1]

    return ceil((vid_height * vid_width + len(trailer)) / (img_height * img_width))

# creates stegano video
def hide(carrier_video, image_message):
    cap = cv2.VideoCapture(carrier_video)
    msg = cv2.imread(image_message)

    req_frame_count = required_frame_count(cap, msg)

    print(req_frame_count)
    
    
    for i in range(req_frame_count):
        ret, frame = cap.read()
        if (ret == False):
            raise Exception('Fucked')


    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        i+=1
       
        print(frame.shape)
        print(msg.shape)
        pass

# while(cap.isOpened()):
#     ret, frame = cap.read()
#     if ret == False:
#         break
# 
#     # cv2.imwrite('kang'+str(i)+'.jpg',frame)
#     print(frame)
# 
#     print(frame.shape)
# 
#     i+=1
#  

# cap.release()
# cv2.destroyAllWindows()

mode = argv[1]

if (mode == '-hide'):
    try:
        carrier_video_path = argv[2]
        image_message_path = argv[3]
        hide(carrier_video_path, image_message_path)
    except Exception as e:
        print('Invalid arguments', e)
elif (mode == '-extract'):
    try:
        stegano_video_path = argv[2]
        extract(stegano_video_path)
    except Exception as e:
        print('Invalid arguments', e)


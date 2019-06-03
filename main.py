from skimage.filters import frangi, hessian
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from skimage.morphology import skeletonize, binary_closing, binary_opening
import cv2
import sys
sys.setrecursionlimit(10000)

ARROW_LENGTH = 30
SEARCH_AREA = 1
MARK_AREA = 1






def load_data(file_name):
    global mat_contents
    mat_contents = sio.loadmat(file_name) #"perfAngio_08.mat"


def get_mat(label):
    return mat_contents.get(label)


def distance_arrow(x, y, length, start_x, start_y, i):
    # print(x,y)

    res = []
    mark = []

    if length == 0:
        res = [(start_x, start_y, x, y)]
        length = ARROW_LENGTH
        start_x, start_y = x, y

    next_level = []
    for new_x in range(x - SEARCH_AREA, x + SEARCH_AREA + 1):
        for new_y in range(y - SEARCH_AREA, y + SEARCH_AREA + 1):

            if new_x > SEARCH_AREA and new_y > SEARCH_AREA \
                    and new_x <= 1024 - SEARCH_AREA and new_y <= 1024 - SEARCH_AREA \
                    and not (new_x == x and new_y == y) and image[i][new_x][new_y] == 1:
                image[i][new_x][new_y] = 0
                mark.append((new_x, new_y))
                next_level.append((new_x, new_y))

    if not next_level:
        end_points = [(x, y)]
    else:
        end_points = []
        for x, y in next_level:
            temp_res, temp_end, temp_mark = distance_arrow(x, y, length - 1, start_x, start_y, i)
            end_points = end_points + temp_end
            res = res + temp_res
            mark = mark + temp_mark

    return res, end_points, mark


def depth_test(x, y, depth, path, i):
    path.add((x, y))
    next_level = []
    for new_x in range(x - SEARCH_AREA, x + SEARCH_AREA + 1):
        for new_y in range(y - SEARCH_AREA, y + SEARCH_AREA + 1):
            if new_x > SEARCH_AREA and new_y > SEARCH_AREA \
                    and new_x <= 1024 - SEARCH_AREA and new_y <= 1024 - SEARCH_AREA \
                    and (new_x, new_y) not in path and image[i][new_x][new_y] == 1:
                next_level.append((new_x, new_y))

    if not next_level:
        return depth
    else:
        temp_depth = []
        for x, y in next_level:
             temp_depth.append(depth_test(x, y, depth + 1, path, i))
        return max(temp_depth)


def find_arrows(start_x, start_y):
    end_points = [(start_x, start_y)]
    res = []
    mark = []

    # iterate through each frame
    # debug !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    for i in range(START_FRAME, 20):
        new_endpoints = []
        # mark_pixel(mark, end_points, image[i])

        # iterate through each arrow endpoint from last frame
        for end_x, end_y in end_points:

            if i != START_FRAME:
                # find start_x and start_y for next frame based on last frame
                start_x, start_y = find_start(end_x, end_y, image[i])
            if start_x != -1:
                temp_res, temp_end, temp_mark = distance_arrow(start_x, start_y, ARROW_LENGTH, start_x, start_y, i)
                res += temp_res
                new_endpoints += temp_end
                mark += temp_mark
        end_points = new_endpoints
        draw_arrow(res, i)


def mark_pixel(mark, end_points, img):
    for x, y in mark:
        for end_x, end_y in end_points:
            if abs(end_x - x) > MARK_AREA and abs(end_y - y) > MARK_AREA:
                for mark_x in range(x - MARK_AREA, x + MARK_AREA + 1):
                    for mark_y in range(y - MARK_AREA, y + MARK_AREA + 1):
                        img[mark_x][mark_y] = 0


# Random Color
def get_cmap(n, name='gist_rainbow'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.cm.get_cmap(name, n)


def draw_arrow(location, i):
    #print("location", location)
    cmap = get_cmap(40)
    for sx, sy, ex, ey in location:
        plt.arrow(sy, sx, ey - sy, ex - sx, width=3, length_includes_head=True, edgecolor="Gray", facecolor=cmap(i), \
                  alpha=1,linewidth=0.5)
    plt.imshow(image[i])
    plt.savefig('File_' + FILE_NAME[10:12]+'_Patient_ID_'+str(Patient_ID)+'_'+str(i)+'.png', dpi=600)
    #plt.show()

def find_start(end_x, end_y, img):
    for mark_x in range(end_x - MARK_AREA, end_x + MARK_AREA + 1):
        for mark_y in range(end_y - MARK_AREA, end_y + MARK_AREA + 1):
            if mark_x > MARK_AREA and mark_y > MARK_AREA \
                    and mark_x <= 1024 - MARK_AREA and mark_y <= 1024-MARK_AREA \
                    and img[mark_x][mark_y] == 1 and (mark_x != end_x and mark_y != end_y):
                return mark_x, mark_y
    return -1, -1


def find_img_start(image_bundle):
    for i in range(20):
        for y in range(200,800):
            for x in range(1023, 1015, -1):
                length = depth_test(x,y,0,set(),i)
                #print("length: ", length)
                if(length > 80):
                    return x,y,i
    return -1,-1,-1


def generate_video():
    video = cv2.VideoWriter('File_' + FILE_NAME[10:12]+'_Patient_ID_'+str(Patient_ID) + '.avi', \
                            cv2.VideoWriter_fourcc(*"MJPG"), 2, (3840, 2880))
    for i in range(4,20):
        img = cv2.imread('File_' + FILE_NAME[10:12]+'_Patient_ID_'+str(Patient_ID)+'_'+str(i)+'.png')
        video.write(img)
    cv2.destroyAllWindows()
    video.release()


# patientId
# CBF
# CBF_cut
# CBV_cut
# Peak
# CBV
# MTT
# TTP
# Tmax
# roi
# X
# frameTime

def main():  # Script takes in one argument: Filename of the data "xxx.mat"
    global FILE_NAME
    global Patient_ID
    global image
    global START_FRAME


    FILE_NAME = sys.argv[1]
    print("File Name: "+ FILE_NAME)
    load_data(FILE_NAME)
    image_origin = get_mat("X")
    Patient_ID = get_mat("patiendId")
    print("Patient ID: " + str(Patient_ID))
    X_image = np.empty([20, 1024, 1024])
    image = np.empty([20, 1024, 1024])
    print("Processing Image")
    for depth in range(20):
        for x in range(1024):
            for y in range(1024):
                X_image[depth][x][y] = image_origin[x][y][depth]

    for y in range(20):
        frangi_image = frangi(X_image[y], beta=2)
        frangi_image = np.rint(frangi_image)
        frangi_image = binary_closing(binary_opening(frangi_image))
        image[y] = skeletonize(frangi_image).astype(np.uint8)

    start_x, start_y, START_FRAME = find_img_start(image)

    print("Start Point: X = " + str(start_x) + ' Y = ' + str(start_y) + ' Start Frame = ' + str(START_FRAME))
    image[START_FRAME][start_x][start_y] = 0
    print("Creating Blood Stream...Saving Images")
    find_arrows(start_x, start_y)
    print("Generating Video")
    generate_video()
    print("Finished")

if __name__ == "__main__":
    main()




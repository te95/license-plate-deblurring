"""
Iterates over image filenames in a directory, generating N new
images with names filenameBLURn for 1<=n<N which are a random
combination of small rotation and translation blur
"""
import os
import numpy as np
import cv2
import matplotlib.image as mpimg
from matplotlib import pyplot as plt
from scipy.misc import imread, imsave, imshow, imresize
from scipy import ndimage
import skimage

def pad_image(img, max_dimensions=(120, 300, 3)):
    # max_dimensions = (78, 245, 3)

    # position padded image randomly
    y_translation = np.random.randint(0, max_dimensions[0] - img.shape[0] + 1)
    x_translation = np.random.randint(0, max_dimensions[1] - img.shape[1] + 1)
   
    y_translation = int((max_dimensions[0] - img.shape[0]) / 2)
    x_translation = int((max_dimensions[1] - img.shape[1]) / 2)

    # padded_img = np.zeros(max_dimensions)
    top = y_translation
    bottom = max_dimensions[0] - img.shape[0] - y_translation
    left = x_translation
    right = max_dimensions[1] - img.shape[1] - x_translation
    padded_img = cv2.copyMakeBorder(img, top=top, bottom=bottom, left=left, right=right,
                                    borderType=cv2.BORDER_CONSTANT, value=(0, 0, 0))

    return padded_img


def gaussian_blur(img):
    kernel_size = 2 * np.random.randint(1, 9) + 1
    sigma = np.random.uniform(0, 3)

    return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigma)


def motion_blur(img):
    rows = img.shape[0]
    cols = img.shape[1]

    # Translation Kernel Size
    tk_size = 15

    # How many random translations
    N = 2

    images = []

    for i in range(N):

        # Creates N random manipulations; either pure translations or rotations

        trans_x = np.random.randint(1, tk_size / 2)
        trans_y = np.random.randint(1, tk_size / 2)
        tx_index = np.random.randint(0, tk_size - trans_x)
        ty_index = np.random.randint(0, tk_size - trans_y)
        rot_angle = np.random.uniform(-3, 3)

        kernel_trans_blur = np.zeros((tk_size, tk_size))

        # Y translation
        if i % 2 == 0:

            kernel_trans_blur[ty_index:ty_index + trans_y, 7] = np.ones(trans_y)
            if trans_y != 0:
                kernel_trans_blur /= trans_y
                # print("transy", trans_y)

        # X Translation
        else:

            kernel_trans_blur[7, tx_index:tx_index + trans_x] = np.ones(trans_x)
            if trans_x != 0:
                kernel_trans_blur /= trans_x
                # print("transx", trans_x)

        rotate = cv2.getRotationMatrix2D((cols, rows), rot_angle, 1)

        which = np.random.randint(10)

        if which < 5:
            # print(i, "is a translation")
            # print("params", kernel_trans_blur)
            trans = cv2.filter2D(img, -1, kernel_trans_blur)

            images.append(trans)

        else:
            # print(i, "is a rotation")
            # To fill in empties later (after rotating some pixels just go black).
            avg_color_per_row = np.average(img, axis=0)
            avg_color = np.average(avg_color_per_row, axis=0)

            first = cv2.warpAffine(img, rotate, (cols, rows))
            second = cv2.warpAffine(first, rotate, (cols, rows))
            final = cv2.addWeighted(first, 0.5, second, 0.5, 0)

            for i in range(final.shape[0]):
                for j in range(final.shape[1]):
                    if np.dot(final[i][j], final[i][j]) < 6:
                        final[i][j] = avg_color
            images.append(final)

    # Blending
    for i in range(4, len(images) - 2):
        images[i] = cv2.addWeighted(images[i + 1], 0.4, images[i + 2], 0.6, 0)

    return images


def cut_image_from_center(img, shape):
    img_shape = img.shape
    y_translation = int(0.5 * (img_shape[0] - shape[0]))
    x_translation = int(0.5 * (img_shape[1] - shape[1]))

    new_img = img[y_translation:y_translation + shape[0], x_translation:x_translation + shape[1]]
    return new_img

def blur_image(img):
    original_shape = img.shape
    if img.shape[1] > 150:
        kernel_size = np.random.randint(5, 18)
    elif img.shape[1] > 100:
        kernel_size = np.random.randint(4, 14)
    elif img.shape[1] > 75:
        kernel_size = np.random.randint(3, 11)
    else:
        kernel_size = np.random.randint(2, 6)
    kernel_size = np.random.randint(12, 31)
    angle = np.random.randint(0, 20)

    img = ndimage.rotate(img, angle, mode='nearest')

    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int(0.5 * kernel_size), :] = 1
    kernel = kernel * 1. / np.sum(kernel)
    blurred = cv2.filter2D(img, -1, kernel)

    blurred = ndimage.rotate(blurred, -angle)
    blurred = cut_image_from_center(blurred, original_shape)
	
    # blurred = gaussian_blur(blurred)
    return blurred


def crop(target_img, train_img, crop_size_target=100, crop_size_train=100):
    if target_img.shape[0] < 40  or target_img.shape[1] < 60:
        target_img = pad_image(target_img, max_dimensions=(max(crop_size_target, target_img.shape[0]),max(int(1.5*crop_size_target), target_img.shape[1]),3))
        train_img = pad_image(train_img, max_dimensions=(max(crop_size_target, train_img.shape[0]),max(int(1.5 * crop_size_target), train_img.shape[1]),3))
    x = np.random.randint(0, target_img.shape[0] - crop_size_target + 1)
    y = np.random.randint(0, target_img.shape[1] - crop_size_target + 1)
    return [(target_img[x:x+crop_size_target, y:y+crop_size_target],
             train_img[x:x+crop_size_target, y:y+crop_size_target])]

def blur_data():
    train_data_path = "./Data/Training_Images/"
    dst_path_targets = "./Data/Cropped/Clear/"
    dst_path_train = "./Data/Cropped/Blurred/"

    for i, f in enumerate(os.listdir(train_data_path)):
        # if "_35" not in f: continue
        if "DS_" in f:
            continue
        print(i)
        os.system('mkdir ./Data/Cropped/Blurred/Training/' + f[:6])
        os.system('mkdir ./Data/Cropped/Clear/' + f[:6])
        os.system('mkdir ./Data/Cropped/Blurred/Validation/' + f[:6])
        dst_path_targets2 = os.path.join(dst_path_targets, f[:6])
        dst_path_train2 = os.path.join(dst_path_train, f[:6])
        img = imread(os.path.join(train_data_path, f))

        for j in range(1, 20):
            initial_rotate = np.random.randint(-5, 6)
            blurred = blur_image(img)
            images = crop(img, blurred)
            for pos, (target, train) in enumerate(images):
                target_filename = f[:-4] + "_pos{:03d}_i{:01d}".format(pos, j) + f[-4:]
                imsave(os.path.join(dst_path_targets2, target_filename), target)
                train_filename = f[:-4] + "_pos{:03d}".format(pos) + "_i{:01d}".format(j) + f[-4:]
                if np.random.rand() < 0.2:
                    train_filename = os.path.join(dst_path_train, "Validation", f[:6], train_filename)
                else:
                    train_filename = os.path.join(dst_path_train, "Training", f[:6], train_filename)
                imsave(train_filename, train)

 
if __name__ == '__main__':
    print(np.random.randint(0, 10))
    os.system('mkdir ./Data/Cropped/')
    os.system('mkdir ./Data/Cropped/Blurred')
    os.system('mkdir ./Data/Cropped/Blurred/Training')
    os.system('mkdir ./Data/Cropped/Blurred/Validation')
    os.system('mkdir ./Data/Cropped/Clear')
    os.system('mkdir ./Data/Cropped/Clear/Training')
    os.system('mkdir ./Data/Cropped/Clear/Validation')
    
    blur_data()

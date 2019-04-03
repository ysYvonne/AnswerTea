#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 12:28:21 2017
@author: Hriddhi Dey

This module contains the ApplyMakeup class.
"""

import itertools
import cv2
from skimage import color
import numpy as np
from scipy import interpolate
from pylab import *
import urllib.request
from io import BytesIO

# from detect_features import DetectLandmarks
from app.visage import DetectLandmarks

intensity = 0.5  # intensity of the blush
mid = 378  # Approx x coordinate of center of the face.

POINT_FILE = './visage/point1.txt'

class ApplyMakeup(DetectLandmarks):
    """
    Class that handles application of color, and performs blending on image.

    Functions available for use:
        1. apply_lipstick: Applies lipstick on passed image of face.
        2. apply_liner: Applies black eyeliner on passed image of face.
    """

    def __init__(self):
        """ Initiator method for class """
        DetectLandmarks.__init__(self)
        self.red_l = 0
        self.green_l = 0
        self.blue_l = 0

        self.red_e = 0
        self.green_e = 0
        self.blue_e = 0

        self.debug = 0

        self.image = 0

        self.width = 0
        self.height = 0

        self.im_copy = 0
        self.lip_x = []
        self.lip_y = []

        self.red_b = 0
        self.green_b = 0
        self.blue_b = 0


    def __read_image(self, filename):
        """ Read image from path forwarded """

        with urllib.request.urlopen(filename) as url:
            s = url.read()

        resp = urllib.request.urlopen(filename)
        img = np.asarray(bytearray(s), dtype="uint8")

        self.image = cv2.imdecode(img, cv2.IMREAD_COLOR)

        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        self.im_copy = self.image.copy()

        self.height, self.width = self.image.shape[:2]

        self.debug = 0

    def _read_image_b(self, filename):

        self.image = cv2.imread(filename)

        self.im_copy = self.image.copy()

        self.height, self.width = self.image.shape[:2]

        self.debug = 0

    def __draw_curve(self, points):
        """ Draws a curve alone the given points by creating an interpolated path. """
        x_pts = []
        y_pts = []
        curvex = []
        curvey = []
        self.debug += 1
        for point in points:
            x_pts.append(point[0])
            y_pts.append(point[1])
        curve = interpolate.interp1d(x_pts, y_pts, 'cubic')
        if self.debug == 1 or self.debug == 2:
            for i in np.arange(x_pts[0], x_pts[len(x_pts) - 1] + 1, 1):
                curvex.append(i)
                curvey.append(int(curve(i)))
        else:
            for i in np.arange(x_pts[len(x_pts) - 1] + 1, x_pts[0], 1):
                curvex.append(i)
                curvey.append(int(curve(i)))
        return curvex, curvey


    def __fill_lip_lines(self, outer, inner):
        """ Fills the outlines of a lip with colour. """
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        count = len(inner[0]) - 1
        last_inner = [inner[0][count], inner[1][count]]
        for o_point, i_point in itertools.zip_longest(
                outer_curve, inner_curve, fillvalue=last_inner
            ):
            line = interpolate.interp1d(
                [o_point[0], i_point[0]], [o_point[1], i_point[1]], 'linear')
            xpoints = list(np.arange(o_point[0], i_point[0], 1))
            self.lip_x.extend(xpoints)
            self.lip_y.extend([int(point) for point in line(xpoints)])
        return


    def __fill_lip_solid(self, outer, inner):
        """ Fills solid colour inside two outlines. """
        inner[0].reverse()
        inner[1].reverse()
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        points = []
        for point in outer_curve:
            points.append(np.array(point, dtype=np.int32))
        for point in inner_curve:
            points.append(np.array(point, dtype=np.int32))
        points = np.array(points, dtype=np.int32)
        self.red_l = int(self.red_l)
        self.green_l = int(self.green_l)
        self.blue_l = int(self.blue_l)
        cv2.fillPoly(self.image, [points], (self.red_l, self.green_l, self.blue_l))


    def __smoothen_color(self, outer, inner):
        """ Smoothens and blends colour applied between a set of outlines. """
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        x_points = []
        y_points = []
        for point in outer_curve:
            x_points.append(point[0])
            y_points.append(point[1])
        for point in inner_curve:
            x_points.append(point[0])
            y_points.append(point[1])
        img_base = np.zeros((self.height, self.width))
        cv2.fillConvexPoly(img_base, np.array(np.c_[x_points, y_points], dtype='int32'), 1)
        img_mask = cv2.GaussianBlur(img_base, (81, 81), 0) #51,51
        img_blur_3d = np.ndarray([self.height, self.width, 3], dtype='float')
        img_blur_3d[:, :, 0] = img_mask
        img_blur_3d[:, :, 1] = img_mask
        img_blur_3d[:, :, 2] = img_mask
        self.im_copy = (img_blur_3d * self.image * 0.7 + (1 - img_blur_3d * 0.7) * self.im_copy).astype('uint8')


    def __draw_liner(self, eye, kind):
        """ Draws eyeliner. """
        eye_x = []
        eye_y = []
        x_points = []
        y_points = []
        for point in eye:
            x_points.append(int(point.split()[0]))
            y_points.append(int(point.split()[1]))
        curve = interpolate.interp1d(x_points, y_points, 'quadratic')
        for point in np.arange(x_points[0], x_points[len(x_points) - 1] + 1, 1):
            eye_x.append(point)
            eye_y.append(int(curve(point)))
        if kind == 'left':
            y_points[0] -= 1
            y_points[1] -= 1
            y_points[2] -= 1
            x_points[0] -= 5
            x_points[1] -= 1
            x_points[2] -= 1
            curve = interpolate.interp1d(x_points, y_points, 'quadratic')
            count = 0
            for point in np.arange(x_points[len(x_points) - 1], x_points[0], -1):
                count += 1
                eye_x.append(point)
                if count < (len(x_points) / 2):
                    eye_y.append(int(curve(point)))
                elif count < (2 * len(x_points) / 3):
                    eye_y.append(int(curve(point)) - 1)
                elif count < (4 * len(x_points) / 5):
                    eye_y.append(int(curve(point)) - 2)
                else:
                    eye_y.append(int(curve(point)) - 3)
        elif kind == 'right':
            x_points[3] += 5
            x_points[2] += 1
            x_points[1] += 1
            y_points[3] -= 1
            y_points[2] -= 1
            y_points[1] -= 1
            curve = interpolate.interp1d(x_points, y_points, 'quadratic')
            count = 0
            for point in np.arange(x_points[len(x_points) - 1], x_points[0], -1):
                count += 1
                eye_x.append(point)
                if count < (len(x_points) / 2):
                    eye_y.append(int(curve(point)))
                elif count < (2 * len(x_points) / 3):
                    eye_y.append(int(curve(point)) - 1)
                elif count < (4 * len(x_points) / 5):
                    eye_y.append(int(curve(point)) - 2)
                elif count:
                    eye_y.append(int(curve(point)) - 3)
        curve = zip(eye_x, eye_y)
        points = []
        for point in curve:
            points.append(np.array(point, dtype=np.int32))
        points = np.array(points, dtype=np.int32)

        self.red_e = int(self.red_e)
        self.green_e = int(self.green_e)
        self.blue_e = int(self.blue_e)
        cv2.fillPoly(self.im_copy, [points], (self.red_e, self.green_e, self.blue_e))
        return


    def __add_color(self, intensity):
        """ Adds base colour to all points on lips, at mentioned intensity. """
        val = color.rgb2lab(
            (self.image[self.lip_y, self.lip_x] / 255.)
            .reshape(len(self.lip_y), 1, 3)
        ).reshape(len(self.lip_y), 3)
        l_val, a_val, b_val = np.mean(val[:, 0]), np.mean(val[:, 1]), np.mean(val[:, 2])
        l1_val, a1_val, b1_val = color.rgb2lab(
            np.array(
                (self.red_l / 255., self.green_l / 255., self.blue_l / 255.)
                ).reshape(1, 1, 3)
            ).reshape(3,)
        l_final, a_final, b_final = (l1_val - l_val) * \
            intensity, (a1_val - a_val) * \
            intensity, (b1_val - b_val) * intensity
        val[:, 0] = np.clip(val[:, 0] + l_final, 0, 100)
        val[:, 1] = np.clip(val[:, 1] + a_final, -127, 128)
        val[:, 2] = np.clip(val[:, 2] + b_final, -127, 128)
        self.image[self.lip_y, self.lip_x] = color.lab2rgb(val.reshape(
            len(self.lip_y), 1, 3)).reshape(len(self.lip_y), 3) * 255


    def __get_points_lips(self, lips_points):
        """ Get the points for the lips. """
        uol = []
        uil = []
        lol = []
        lil = []
        for i in range(0, 14, 2):
            uol.append([int(lips_points[i]), int(lips_points[i + 1])])
        for i in range(12, 24, 2):
            lol.append([int(lips_points[i]), int(lips_points[i + 1])])
        lol.append([int(lips_points[0]), int(lips_points[1])])
        for i in range(24, 34, 2):
            uil.append([int(lips_points[i]), int(lips_points[i + 1])])
        for i in range(32, 40, 2):
            lil.append([int(lips_points[i]), int(lips_points[i + 1])])
        lil.append([int(lips_points[24]), int(lips_points[25])])
        return uol, uil, lol, lil


    def __get_curves_lips(self, uol, uil, lol, lil):
        """ Get the outlines of the lips. """
        uol_curve = self.__draw_curve(uol)
        uil_curve = self.__draw_curve(uil)
        lol_curve = self.__draw_curve(lol)
        lil_curve = self.__draw_curve(lil)
        return uol_curve, uil_curve, lol_curve, lil_curve


    def __fill_color(self, uol_c, uil_c, lol_c, lil_c):
        """ Fill colour in lips. """
        self.__fill_lip_lines(uol_c, uil_c)
        self.__fill_lip_lines(lol_c, lil_c)
        self.__add_color(1)
        self.__fill_lip_solid(uol_c, uil_c)
        self.__fill_lip_solid(lol_c, lil_c)
        self.__smoothen_color(uol_c, uil_c)
        self.__smoothen_color(lol_c, lil_c)


    def __create_eye_liner(self, eyes_points):
        """ Apply eyeliner. """
        left_eye = eyes_points[0].split('\n')
        right_eye = eyes_points[1].split('\n')
        right_eye = right_eye[0:4]
        self.__draw_liner(left_eye, 'left')
        self.__draw_liner(right_eye, 'right')


    def apply_lipstick(self, filename, rlips, glips, blips):
        """
        Applies lipstick on an input image.
        ___________________________________
        Args:
            1. `filename (str)`: Path for stored input image file.
            2. `red (int)`: Red value of RGB colour code of lipstick shade.
            3. `blue (int)`: Blue value of RGB colour code of lipstick shade.
            4. `green (int)`: Green value of RGB colour code of lipstick shade.

        Returns:
            `filepath (str)` of the saved output file, with applied lipstick.

        """

        self.red_l = rlips
        self.green_l = glips
        self.blue_l = blips

        self.__read_image(filename)

        lips = self.get_lips(self.image)
        lips = list([point.split() for point in lips.split('\n')])
        lips_points = [item for sublist in lips for item in sublist]
        uol, uil, lol, lil = self.__get_points_lips(lips_points)
        uol_c, uil_c, lol_c, lil_c = self.__get_curves_lips(uol, uil, lol, lil)
        self.__fill_color(uol_c, uil_c, lol_c, lil_c)
        self.im_copy = cv2.cvtColor(self.im_copy, cv2.COLOR_BGR2RGB)

        name = 'color_' + str(self.red_l) + '_' + str(self.green_l) + '_' + str(self.blue_l)

        # file_name = 'result_lipstick_' + name + '.jpg'
        # cv2.imwrite(file_name, self.im_copy)

        r, outputImage = cv2.imencode('.jpg', self.im_copy)
        if False == r:
            raise Exception('Error encoding image')

        img_stream = BytesIO(outputImage)

        return img_stream


    def apply_liner(self, filename):
        """
        Applies lipstick on an input image.
        ___________________________________
        Args:
            1. `filename (str)`: Path for stored input image file.

        Returns:
            `filepath (str)` of the saved output file, with applied lipstick.

        """
        self.__read_image(filename)
        liner = self.get_upper_eyelids(self.image)
        eyes_points = liner.split('\n\n')
        self.__create_eye_liner(eyes_points)
        self.im_copy = cv2.cvtColor(self.im_copy, cv2.COLOR_BGR2RGB)

        name = 'color_' + str(self.red_l) + '_' + str(self.green_l) + '_' + str(self.blue_l)

        # file_name = 'result_lipstick_' + name + '.jpg'
        # cv2.imwrite(file_name, self.im_copy)

        r, outputImage = cv2.imencode('.jpg', self.im_copy)
        if False == r:
            raise Exception('Error encoding image')

        img_stream = BytesIO(outputImage)

        return img_stream

######################################################################################################

    def get_boundary_points(self, x, y):
        tck, u = interpolate.splprep([x, y], s=0, per=1)
        unew = np.linspace(u.min(), u.max(), 1000)
        xnew, ynew = interpolate.splev(unew, tck, der=0)
        tup = c_[xnew.astype(int), ynew.astype(int)].tolist()
        coord = list(set(tuple(map(tuple, tup))))
        coord = np.array([list(elem) for elem in coord])

        return np.array(coord[:, 0], dtype=np.int32), np.array(coord[:, 1], dtype=np.int32)

    def get_interior_points(self, x, y):
        intx = []
        inty = []

        def ext(a, b, i):
            a, b = round(a), round(b)
            intx.extend(arange(a, b, 1).tolist())
            inty.extend((ones(b - a) * i).tolist())

        x, y = np.array(x), np.array(y)
        xmin, xmax = amin(x), amax(x)
        xrang = np.arange(xmin, xmax + 1, 1)
        for i in xrang:
            ylist = y[where(x == i)]
            ext(amin(ylist), amax(ylist), i)

        return np.array(intx, dtype=np.int32), np.array(inty, dtype=np.int32)

    def apply_blush_color(self):

        val = color.rgb2lab((self.image / 255.)).reshape(self.width * self.height, 3)
        L, A, B = mean(val[:, 0]), mean(val[:, 1]), mean(val[:, 2])
        L1, A1, B1 = color.rgb2lab(np.array((self.red_b / 255., self.green_b / 255., self.blue_b / 255.)).reshape(1, 1, 3)).reshape(3, )
        ll, aa, bb = (L1 - L) * intensity, (A1 - A) * intensity, (B1 - B) * intensity
        val[:, 0] = np.clip(val[:, 0] + ll, 0, 100)
        val[:, 1] = np.clip(val[:, 1] + aa, -127, 128)
        val[:, 2] = np.clip(val[:, 2] + bb, -127, 128)
        self.image = color.lab2rgb(val.reshape(self.height, self.width, 3)) * 255

    def smoothen_blush(self, x, y):

        imgBase = zeros((self.height, self.width))
        cv2.fillConvexPoly(imgBase, np.array(c_[x, y], dtype='int32'), 1)
        imgMask = cv2.GaussianBlur(imgBase, (51, 51), 0)
        imgBlur3D = np.ndarray([self.height, self.width, 3], dtype='float')
        imgBlur3D[:, :, 0] = imgMask
        imgBlur3D[:, :, 1] = imgMask
        imgBlur3D[:, :, 2] = imgMask
        self.im_copy = (imgBlur3D * self.image + (1 - imgBlur3D) * self.im_copy).astype('uint8')

    def apply_blush(self, filename, Rg, Gg, Bg):

        self.red_b = Rg
        self.green_b = Gg
        self.blue_b = Bg

        self._read_image_b(filename)

        points = np.loadtxt(POINT_FILE)
        x, y = points[0:5, 0], points[0:5, 1]
        x, y = self.get_boundary_points(x, y)
        x, y = self.get_interior_points(x, y)

        self.apply_blush_color()
        self.smoothen_blush(x, y)
        self.smoothen_blush(2 * mid * ones(len(x)) - x, y)

        name = 'color_' + str(self.red_l) + '_' + str(self.green_l) + '_' + str(self.blue_l)

        # file_name = 'result_lipstick_' + name + '.jpg'
        # cv2.imwrite(file_name, self.im_copy)

        r, outputImage = cv2.imencode('.jpg', self.im_copy)
        if False == r:
            raise Exception('Error encoding image')

        img_stream = BytesIO(outputImage)

        return img_stream





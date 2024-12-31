from typing import List

import numpy as np
import cv2 as cv


def _getMSSISM(i1, i2):
    """
    Taken from: https://docs.opencv.org/4.x/d5/dc4/tutorial_video_input_psnr_ssim.html
    """
    C1 = 6.5025
    C2 = 58.5225
    # INITS

    I1 = np.float32(i1)  # cannot calculate on one byte large values
    I2 = np.float32(i2)

    I2_2 = I2 * I2  # I2^2
    I1_2 = I1 * I1  # I1^2
    I1_I2 = I1 * I2  # I1 * I2
    # END INITS

    # PRELIMINARY COMPUTING
    mu1 = cv.GaussianBlur(I1, (11, 11), 1.5)
    mu2 = cv.GaussianBlur(I2, (11, 11), 1.5)

    mu1_2 = mu1 * mu1
    mu2_2 = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_2 = cv.GaussianBlur(I1_2, (11, 11), 1.5)
    sigma1_2 -= mu1_2

    sigma2_2 = cv.GaussianBlur(I2_2, (11, 11), 1.5)
    sigma2_2 -= mu2_2

    sigma12 = cv.GaussianBlur(I1_I2, (11, 11), 1.5)
    sigma12 -= mu1_mu2

    t1 = 2 * mu1_mu2 + C1
    t2 = 2 * sigma12 + C2
    t3 = t1 * t2  # t3 = ((2*mu1_mu2 + C1).*(2*sigma12 + C2))

    t1 = mu1_2 + mu2_2 + C1
    t2 = sigma1_2 + sigma2_2 + C2
    t1 = t1 * t2  # t1 =((mu1_2 + mu2_2 + C1).*(sigma1_2 + sigma2_2 + C2))

    ssim_map = cv.divide(t3, t1)  # ssim_map =  t3./t1;

    mssim = cv.mean(ssim_map)  # mssim = average of ssim map
    return mssim


def _calc_confidence(value: float, alarm_threshold: float) -> float:
    delta = abs(alarm_threshold - value)
    if delta > 0.1:
        return 1.0
    else:
        return delta * 10


def calculate_ssim_score(raw_rgb_images: List[np.ndarray], resize_factor: float = 0.1,
                         alarm_threshold: float = 0.9) -> float:
    """
    Calculate if a set of images is similar or not

    :param raw_rgb_images: List of raw, rgb images
    :param resize_factor: Scale down factor
    :param alarm_threshold: SSIM scores lower than this number will be threted as dissimilar
    :return: Similarity score in the range of [0,1] where one is very certainly dissimilar and zero indicates most likely
    the same images.
    """
    # preprocessing
    preprocessed_images = []
    for raw_image in raw_rgb_images:
        img_gray = cv.cvtColor(raw_image, cv.COLOR_BGR2GRAY)
        img_scaled = cv.resize(img_gray, None, fx=resize_factor, fy=resize_factor, interpolation=cv.INTER_LINEAR)
        img_equ = cv.equalizeHist(img_scaled)
        preprocessed_images.append(img_equ)

    # calculate scores
    scores = []
    for i in range(len(raw_rgb_images)):
        scores.append(_getMSSISM(preprocessed_images[i - 1], preprocessed_images[i]))

    verdicts = map(lambda sc: sc[0] < alarm_threshold, scores)
    if any(verdicts):
        return _calc_confidence(min(verdicts), alarm_threshold)
    else:
        return 0.0

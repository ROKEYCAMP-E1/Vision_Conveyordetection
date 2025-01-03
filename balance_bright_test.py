import cv2
import numpy as np

def calculate_brightness(image):
    """이미지의 평균 밝기를 계산하는 함수"""
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.mean(gray_image)

def adjust_brightness(image, target_brightness):
    """이미지의 밝기를 target_brightness에 맞추어 조절하는 함수"""
    current_brightness = calculate_brightness(image)
    brightness_difference = target_brightness - current_brightness 
    # 밝기 조절
    adjusted_image = cv2.convertScaleAbs(image, alpha=1, beta=brightness_difference)
    return adjusted_image


# # 밝기를 맞추고자 하는 이미지 목록
 # 파일명을 리스트로 추가

def export_img(standard,iamge):
    

        # 밝기 조절
    adjusted_image = adjust_brightness(iamge, standard)

    return adjusted_image


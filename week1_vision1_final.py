# Renew.py
from datetime import datetime   
import sys
import os
import cv2
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from balance_bright_test import calculate_brightness,adjust_brightness,export_img
from insert_data import insert_data
import sqlite3

conn = sqlite3.connect('team1_v3')
cursor = conn.cursor()

datetime_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
adjust_path='/home/rokey/Desktop/ROKEY/대면/1주차/VisionSystemProject/Results_v2.5/Negative/test_defective1_result.jpg'
reference_image = cv2.imread(adjust_path)
target_brightness = calculate_brightness(reference_image)

ACCESS_KEY = "i785lgd7L83fXuMWk7fcWaNkE0Xsqrt43cgDzFWl"
version = "v3"
folder_path = "/home/rokey/Desktop/ROKEY/대면/1주차/VisionSystemProject/Test_dataset_v2"
file_path = [os.path.join(folder_path, file) for file in os.listdir(folder_path)]
colors = { "RASPBERRY PICO" : [135, 206, 235], "BOOTSEL":[255, 255, 0], "OSCILLATOR":[0, 255, 0], "HOLE":[255, 0, 255], "CHIPSET": [0,0,255], "USB":[255, 165, 0], "CRACK" : [128,128,128], "IMPURITIES":[255,0,0]}
url = {
    "v1" : "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/603adc4d-91cd-41f6-a55b-7e99c8c9bc24/inference",
    "v2" : "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/da8ff7e5-aa08-4e7d-8a12-af701e60f41e/inference",
    "v2.4" : "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/b46fa1b9-555c-44bb-b94b-c3d4a859c65c/inference",
    "v3" : "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/bb4341be-a6f5-47cf-810b-b95f17a398d3/inference"
}

# 클래스 번호에 따라 클래스명을 정의하는 사전
class_map = {
    1: "USB",
    2: "RASPBERRY PICO",
    3: "BOOTSEL",
    4: "OSCILLATOR",
    5: "HOLE",
    6: "CHIPSET",
    7: "CRACK",
    8: "IMPURITIES"
}

def convert_bbox_format(bbox):
    # bbox가 [x1, y1, width, height] 형식인 경우, [x1, y1, x2, y2]로 변환
    x1, y1, width, height = bbox
    x2 = x1 + width
    y2 = y1 + height
    return [x1, y1, x2, y2]

'''
# 비동기 API 요청을 처리할 스레드 클래스 정의
class ImageProcessingThread(QThread):
    result_signal = pyqtSignal(str, np.ndarray, dict, dict)  # 결과를 UI에 전달할 시그널

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        img, objects = self.process_image(self.image_path)
        img, bbox_dict, score_dict = draw_detections(img, objects)
        self.result_signal.emit(self.image_path, img, bbox_dict, score_dict)

    def process_image(self, image_path):
        with open(image_path, "rb") as image:
            response = requests.post(
                url[version],
                auth=HTTPBasicAuth("kdt2024_1-21", ACCESS_KEY),
                headers={"Content-Type": "image/jpeg"},
                data=image
            )
            objects = response.json().get("objects", [])
            return image_path, objects
            '''

def process_image(image_path):
    with open(image_path, "rb") as image:
        response = requests.post(url[version], auth=HTTPBasicAuth("kdt2024_1-21", ACCESS_KEY),
                                 headers={"Content-Type": "image/jpeg"}, data=image)
        objects = response.json().get("objects", [])
        return image_path, objects

def draw_detections(image_path, objects):
    img = cv2.imread(image_path)
    img = export_img(target_brightness, img) # 밝기
    bbox_dict = {key: [] for key in colors}
    score_dict = {key: [] for key in colors}
    for obj in objects:
        class_name, score, box = obj["class"], obj["score"], obj["box"]
        # field에서 적용
        #box = convert_bbox_format(box) 
        if score >= 0.7:
            score_dict[class_name].append(score)
            bbox_dict[class_name].append(box)
            cv2.rectangle(img, tuple(box[:2]), tuple(box[2:]), colors[class_name], 1)
            # 클래스 이름은 기본 크기로
            cv2.putText(img, class_name, tuple(box[:2]), cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors[class_name], 1, cv2.LINE_AA)

            ''''
            # score는 클래스 이름보다 작은 크기로 아래쪽에 표시
            score_position = (box[0], box[1] -15)  # 약간 아래로 이동하여 표시
            cv2.putText(img, f"{score:.2f}", score_position, cv2.FONT_HERSHEY_SIMPLEX, 0.3, colors[class_name], 1, cv2.LINE_AA)
            '''

    return img, bbox_dict, score_dict

def save_result(img, base_name, quality,reason_text):

    insert_data(datetime_value, base_name, quality, defect_reason= reason_text)
    result_folder = "Positive" if quality else "Negative"
    os.makedirs(f"Results_{version}/{result_folder}", exist_ok=True)
    img_name = f"Results_{version}/{result_folder}/{base_name}_result.jpg"
    cv2.imwrite(img_name, img)
    

# 메인 클래스
class QualityCheckApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quality Check System")
        self.setGeometry(100, 100, 1800, 1000)
        
        self.cumulative_pass = 0
        self.cumulative_fail = 0
        self.current_index = 0
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        display_layout = QHBoxLayout()
        
        # 이미지와 품질 상태 표시 영역
        image_display_layout = QVBoxLayout()
        
        # 품질 결과와 이유 표시 레이블 (이미지 위에 배치)
        self.quality_label = QLabel()
        self.quality_label.setAlignment(Qt.AlignCenter)
        quality_font = QFont("Arial", 18, QFont.Bold)  # 폰트 크기를 더 키움
        self.quality_label.setFont(quality_font)
        self.quality_label.setStyleSheet("background-color: rgba(255, 255, 255, 150);")
        self.quality_label.setContentsMargins(0, -10, 0, 0)  # 상단 마진 조정으로 이미지가 위로 올라가도록 함
        image_display_layout.addWidget(self.quality_label)

        # 이미지 디스플레이
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(1000, 800)
        self.image_label.setStyleSheet("background-color: rgba(255, 255, 255, 150);")  # 약간 투명한 배경 설정
        image_display_layout.addWidget(self.image_label)
        
        display_layout.addLayout(image_display_layout)

        # 오른쪽에 통계와 테이블을 담을 QVBoxLayout
        tables_layout = QVBoxLayout()
        
        # 누적 통계 레이블
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        stats_font = QFont("Arial", 16, QFont.Bold)  # 폰트 크기를 더 키움
        self.stats_label.setFont(stats_font)
        self.update_stats_label()
        tables_layout.addWidget(self.stats_label)

        # 첫 번째 통계 테이블
        self.table_widget1 = QTableWidget()
        self.table_widget1.setColumnCount(2)
        self.table_widget1.setHorizontalHeaderLabels(["부품 이름", "Count"])
        self.table_widget1.setFont(QFont("Arial", 20))  # 테이블 글씨 크기 증가
        self.table_widget1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget1.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 행 높이 자동 조정
        tables_layout.addWidget(self.table_widget1)

        # 두 번째 통계 테이블
        self.table_widget2 = QTableWidget()
        self.table_widget2.setColumnCount(2)
        self.table_widget2.setHorizontalHeaderLabels(["불량 원인", "Count"])
        self.table_widget2.setFont(QFont("Arial", 20))  # 테이블 글씨 크기 증가
        
        #self.table_widget2.setRowHeight(0, 500)  # 각 행의 높이 증가
        #self.table_widget2.setColumnWidth(0, 300)  # 첫 번째 열 너비 증가
        #self.table_widget2.setColumnWidth(1, 300)  # 두 번째 열 너비 증가
        
        
        self.table_widget2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget2.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 행 높이 자동 조정

        tables_layout.addWidget(self.table_widget2)

        display_layout.addLayout(tables_layout)
        main_layout.addLayout(display_layout)

        self.setCentralWidget(main_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.request_next_image_processing)
        self.timer.start(1000)

        self.current_thread = None

    def update_stats_label(self):
        self.stats_label.setText(
            f"<h2><span style='color:green;'>누적 양품 수: {self.cumulative_pass}</span> | "
            f"<span style='color:red;'>누적 불량품 수: {self.cumulative_fail}</span></h2>"
        )


    def request_next_image_processing(self):
        if self.current_index < len(file_path):
            image_path = file_path[self.current_index]
            
            if self.current_thread is None or not self.current_thread.isRunning():
                self.current_thread = ImageProcessingThread(image_path)
                self.current_thread.result_signal.connect(self.update_display)
                self.current_thread.start()

            self.current_index += 1

    def update_display(self, image_path, img, bbox_dict, score_dict):
        quality, reasons = self.check_quality(bbox_dict, score_dict)

        if quality:
            self.cumulative_pass += 1
            quality_text = "Pass"
            reason_text = ""
        else:
            self.cumulative_fail += 1
            quality_text = "Fail"
            reason_text = ", ".join(reasons)

        self.display_image(img)
        self.update_table(bbox_dict)
        self.update_quality_label(quality_text, reason_text)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        save_result(img, base_name, quality,reason_text)

        self.update_stats_label()

    def display_image(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_table(self, bbox_dict):
        class_data = {k: len(v) for k, v in bbox_dict.items() if k not in ["IMPURITIES", "CRACK"]}
        self.table_widget1.setRowCount(len(class_data))
        for row, (cls, count) in enumerate(class_data.items()):
            item_cls = QTableWidgetItem(cls)
            item_cls.setFont(QFont("Arial", 20))
            item_count = QTableWidgetItem(str(count))
            item_count.setFont(QFont("Arial", 20))
            self.table_widget1.setItem(row, 0, item_cls)
            self.table_widget1.setItem(row, 1, item_count)
        
        defect_data = {k: len(v) for k, v in bbox_dict.items() if k in ["IMPURITIES", "CRACK"]}
        self.table_widget2.setRowCount(len(defect_data))
        for row, (defect, count) in enumerate(defect_data.items()):
            item_defect = QTableWidgetItem(defect)
            item_defect.setFont(QFont("Arial", 20))
            item_count = QTableWidgetItem(str(count))
            item_count.setFont(QFont("Arial", 20))
            self.table_widget2.setItem(row, 0, item_defect)
            self.table_widget2.setItem(row, 1, item_count)

    def update_quality_label(self, quality_text, reason_text):
        # 양품일 경우 모든 글자 초록색, 불량일 경우 모든 글자 빨간색
        color = "green" if quality_text == "Pass" else "red"
        reason_display = f"<p style='color:{color};'><b>불량 사유: </b>{reason_text}</p>" if reason_text else ""
        
        # 품질 상태가 항상 표시되도록 설정
        self.quality_label.setText(
            f"<h1 style='color:{color};'>품질 상태: {quality_text}</h1>{reason_display}"
        )


    def check_quality(self, bbox_dict, score_dict):
        reasons = []
        if any(score < 0.72 for score in score_dict["RASPBERRY PICO"]):
            reasons.append("Raspberry pico is distort")
            return False, reasons
        
        for key, boxes in bbox_dict.items():
            if key in ["RASPBERRY PICO", "BOOTSEL", "OSCILLATOR", "CHIPSET", "USB"] and len(boxes) == 1:
                continue
            if key == "HOLE":
                continue
            if (key == "IMPURITIES" and len(boxes) >=1) or (key == "CRACK" and len(boxes) >=1):
                reasons.append(f"{key}")
                return False, reasons
            if key in ["IMPURITIES", "CRACK"]:
                continue
            else:
                reasons.append("lacking elements")
                return False, reasons

        x_1, y_1, x_2, y_2 = bbox_dict["RASPBERRY PICO"][0]
        
        area1 = [x_1, y_1, x_2, (y_1 + y_2) / 2]
        area2 = [x_1, (y_1 + y_2) / 2, x_2, y_2]

        area1_count = 0
        area2_count = 0
            
        for bbox in bbox_dict["HOLE"]:
            hx1, hy1, hx2, hy2 = bbox
            if hx1 >= area1[0] and hx2 <= area1[2] and hy1 >= area1[1] and hy2 <= area1[3]:
                area1_count += 1
            elif hx1 >= area2[0] and hx2 <= area2[2] and hy1 >= area2[1] and hy2 <= area2[3]:
                area2_count += 1

        if not (area1_count == 2 and area2_count == 2):
            reasons.append(f"Hole is missing")
            return False, reasons
        
        return True, reasons


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QualityCheckApp()
    main_window.show()
    sys.exit(app.exec_())
    
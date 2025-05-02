import sys
import threading
import requests
import time
import webbrowser
import urllib.parse
import json
import urllib3
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QTextEdit, QLabel, QComboBox, QMessageBox, QFrame
)
from PyQt5.QtGui import QIcon
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def resource_path(relative_path):
    """PyInstaller 빌드에서도 리소스 파일 경로 인식"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class MainWindow(QWidget):
    BASE_URL = "https://kr.landroverkorea.co.kr:6443/parts-info/parts_list.asp"
    DELAY = 0.01

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FindLandRoverPartsKR")
        self.setWindowIcon(QIcon(resource_path('landrover_tad_icon.ico')))
        self.resize(800, 600)

        self.stop_event = threading.Event()
        self.found_pages = []

        self.load_options()
        self.init_ui()

    def load_options(self):
        """JSON 옵션 파일 로드 (빌드된 exe에서도 경로 문제없게)"""
        options_path = resource_path("options.json")
        with open(options_path, "r", encoding="utf-8") as f:
            options = json.load(f)
        self.car_models = options["car_models"]
        self.parts_groups = options["parts_groups"]

    def init_ui(self):
        layout = QVBoxLayout()

        # 차량 선택
        car_layout = QHBoxLayout()
        car_label = QLabel("<font color='red'>*</font> 차량 선택:")
        self.car_combo = QComboBox()
        self.car_combo.addItems(self.car_models)
        if "DEFENDER (L663)" in self.car_models:
            index = self.car_models.index("DEFENDER (L663)")
            self.car_combo.setCurrentIndex(index)
        car_layout.addWidget(car_label)
        car_layout.addWidget(self.car_combo)
        layout.addLayout(car_layout)

        # 부품 그룹 선택
        group_layout = QHBoxLayout()
        group_label = QLabel("부품 그룹 선택:")
        self.group_combo = QComboBox()
        self.group_combo.addItem("선택")
        self.group_combo.addItems(self.parts_groups)
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)

        # 검색어 입력
        input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력...")
        input_layout.addWidget(self.search_input)

        self.start_button = QPushButton("검색 시작")
        self.start_button.clicked.connect(self.start_search)
        input_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("검색 중단")
        self.stop_button.clicked.connect(self.stop_search)
        input_layout.addWidget(self.stop_button)

        layout.addLayout(input_layout)

        self.search_input.textChanged.connect(self.toggle_start_button)
        self.start_button.setEnabled(False)

        self.status_label = QLabel("페이지 검색이 준비되었습니다. 검색 시작 시 진행정도를 표시합니다.")
        layout.addWidget(self.status_label)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        self.link_info_label = QLabel("링크를 클릭하면 해당 페이지를 열람합니다.")
        self.link_info_label.setStyleSheet("color: gray; font-size: 8pt;")
        layout.addWidget(self.link_info_label)

        self.result_list = QListWidget()
        self.result_list.itemDoubleClicked.connect(self.open_url)
        layout.addWidget(self.result_list)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def toggle_start_button(self, text):
        self.start_button.setEnabled(bool(text.strip()))

    def log(self, message):
        self.log_output.append(message)

    def start_search(self):
        car_model = self.car_combo.currentText()
        parts_group = self.group_combo.currentText()
        search_term = self.search_input.text().strip()

        if not car_model:
            QMessageBox.warning(self, "경고", "차량을 선택하세요!")
            return

        if not search_term:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요!")
            return

        if parts_group == "선택":
            parts_group = ""

        self.stop_event.clear()
        self.result_list.clear()
        self.log_output.clear()
        self.found_pages.clear()
        self.status_label.setText("검색 시작됨")

        self.log(f"🔍 검색 시작: 차량={car_model}, 그룹={parts_group}, 검색어={search_term}")

        threading.Thread(
            target=self.search_thread,
            args=(car_model, parts_group, search_term),
            daemon=True
        ).start()

    def stop_search(self):
        self.stop_event.set()
        self.log("🛑 검색 중단 요청됨")

    def search_thread(self, car_model, parts_group, search_term):
        page = 1
        while True:
            if self.stop_event.is_set():
                self.log("검색 중단됨")
                self.status_label.setText("검색 중단됨")
                break

            url = (
                f"{self.BASE_URL}"
                f"?intPage={page}"
                f"&sPL_CarModel={urllib.parse.quote(car_model)}"
                f"&sPL_PartsGroup={urllib.parse.quote(parts_group)}"
            )

            try:
                resp = requests.get(url, verify=False, timeout=10)
                content = resp.text

                if "등록된 데이터가 없습니다." in content:
                    self.log(f"🔍 모든 페이지({page - 1})에서 검색 완료")
                    self.status_label.setText(f"검색 완료 (총 {page - 1} 페이지)")
                    break

                soup = BeautifulSoup(content, 'html.parser')
                rows = soup.select('tbody tr')

                found_in_part_number = False
                found_in_part_name = False

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        part_number = cols[3].get_text(strip=True)
                        part_name = cols[4].get_text(strip=True)

                        if search_term.lower() in part_number.lower():
                            found_in_part_number = True
                        if search_term.lower() in part_name.lower():
                            found_in_part_name = True

                if found_in_part_number or found_in_part_name:
                    found_fields = []
                    if found_in_part_number:
                        found_fields.append("부품번호")
                    if found_in_part_name:
                        found_fields.append("부품명")

                    fields_str = ", ".join(found_fields)
                    message = f"✅ {page} 페이지의 {fields_str}에서 검색어 '{search_term}'를 발견했습니다."

                    self.log(message)
                    self.result_list.addItem(f"{page}: {url}")
                    self.found_pages.append(url)

                self.status_label.setText(f"검색 중... 현재 {page} 페이지")

            except Exception as e:
                self.log(f"[에러] {page} 페이지 요청 실패: {e}")

            page += 1
            time.sleep(self.DELAY)

        self.log("🔍 검색 루프 종료")

    def open_url(self, item):
        url = item.text().split(": ", 1)[1]
        webbrowser.open(url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

import sys
import os
import threading
import requests
import time
import webbrowser
import urllib.parse
import json
import urllib3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QListWidget, QTextEdit, QLabel, QComboBox, QMessageBox, QFrame, QInputDialog
)
from PyQt5.QtGui import QIcon
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_data_file_path(filename):
    return resource_path(os.path.join("data", filename))


class MainWindow(QWidget):
    BASE_URL = "https://kr.landroverkorea.co.kr:6443/parts-info/parts_list.asp"
    DELAY = 0.01

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FindLandRoverPartsKR (v2)")
        self.setWindowIcon(QIcon(resource_path('landrover_tad_icon.ico')))
        self.resize(800, 600)

        self.stop_event = threading.Event()
        self.data_file = ""
        self.current_applied_date = None
        self.latest_applied_date = None
        self.loaded_data = []

        self.load_options()
        self.init_ui()

    def load_options(self):
        options_path = resource_path("options.json")
        with open(options_path, "r", encoding="utf-8") as f:
            options = json.load(f)
        self.car_models = options["car_models"]

    def init_ui(self):
        layout = QVBoxLayout()

        # 차량 선택
        car_layout = QHBoxLayout()
        car_label = QLabel("<font color='red'>*</font> 차량 선택:")
        self.car_combo = QComboBox()
        self.car_combo.addItem("-선택-")
        self.car_combo.addItems(self.car_models)
        car_layout.addWidget(car_label)
        car_layout.addWidget(self.car_combo)
        layout.addLayout(car_layout)

        # 상태 라벨
        self.status_label = QLabel("차량 선택 후 데이터 상태를 확인합니다.")
        layout.addWidget(self.status_label)

        # 데이터 수집 버튼
        self.collect_button = QPushButton("데이터 수집")
        self.collect_button.setEnabled(False)
        self.collect_button.clicked.connect(self.start_data_collection)
        layout.addWidget(self.collect_button)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        # 검색 입력
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어 입력...")
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search_data)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.link_info_label = QLabel("검색 결과를 더블클릭하면 원본 페이지가 열립니다.")
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

        self.car_combo.currentIndexChanged.connect(self.check_data_status)

    def log(self, message):
        self.log_output.append(message)

    def check_data_status(self):
        car_model = self.car_combo.currentText()
        if car_model == "-선택-":
            self.status_label.setText("차량을 선택하세요.")
            self.collect_button.setEnabled(False)
            return

        safe_filename = car_model.replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and')
        self.data_file = f"{safe_filename}.json"
        data_file_path = get_data_file_path(self.data_file)

        if os.path.exists(data_file_path):
            with open(data_file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.current_applied_date = saved_data.get("적용일자")
                self.log(f"로컬 데이터 적용일자: {self.current_applied_date}")
        else:
            self.current_applied_date = None
            self.log("저장된 데이터 없음")

        self.status_label.setText("서버에서 최신 적용일자 확인 중...")
        threading.Thread(target=self.fetch_latest_applied_date, args=(car_model,), daemon=True).start()

    def fetch_latest_applied_date(self, car_model):
        url = f"{self.BASE_URL}?intPage=1&sPL_CarModel={urllib.parse.quote(car_model)}"
        try:
            resp = requests.get(url, verify=False, timeout=10)
            content = resp.text
            soup = BeautifulSoup(content, 'html.parser')
            rows = soup.select('tbody tr')
            applied_dates = []

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    date = cols[6].get_text(strip=True)
                    if date:
                        applied_dates.append(date)

            if applied_dates:
                self.latest_applied_date = applied_dates[0]
                self.log(f"서버 적용일자: {self.latest_applied_date}")

                if self.current_applied_date == self.latest_applied_date:
                    self.status_label.setText("✔ 최신 데이터 사용 중")
                    self.collect_button.setEnabled(False)
                else:
                    self.status_label.setText("⚠ 새 데이터가 있습니다 → 데이터 수집 필요")
                    self.collect_button.setEnabled(True)
            else:
                self.status_label.setText("서버에서 적용일자를 찾을 수 없습니다.")
                self.collect_button.setEnabled(True)

        except Exception as e:
            self.log(f"[에러] 적용일자 확인 실패: {e}")
            self.status_label.setText("적용일자 확인 실패")
            self.collect_button.setEnabled(True)

    def start_data_collection(self):
        pin, ok = QInputDialog.getText(self, "관리자 인증", "관리자만 데이터 수집이 가능합니다.\n활성 PIN 번호를 입력하세요:", echo=QLineEdit.Password)
        if not ok or pin != "1604":
            QMessageBox.warning(self, "경고", "잘못된 PIN 번호입니다. 데이터 수집 권한이 없습니다.")
            self.log("잘못된 PIN 번호로 데이터 수집 시도")
            return

        car_model = self.car_combo.currentText()
        if car_model == "-선택-":
            QMessageBox.warning(self, "경고", "차량을 선택하세요!")
            return

        self.collect_button.setEnabled(False)
        self.stop_event.clear()
        threading.Thread(target=self.collect_data_thread, args=(car_model,), daemon=True).start()

    def collect_data_thread(self, car_model):
        page = 1
        collected = []
        while True:
            if self.stop_event.is_set():
                self.log("데이터 수집 중단됨")
                break

            url = f"{self.BASE_URL}?intPage={page}&sPL_CarModel={urllib.parse.quote(car_model)}"
            try:
                resp = requests.get(url, verify=False, timeout=10)
                content = resp.text

                if "등록된 데이터가 없습니다." in content:
                    self.log(f"데이터 수집 완료 ({len(collected)}건)")
                    save_data = {
                        "차량": car_model,
                        "적용일자": self.latest_applied_date or "",
                        "데이터": collected
                    }
                    os.makedirs(get_data_file_path(""), exist_ok=True)
                    with open(get_data_file_path(self.data_file), "w", encoding="utf-8") as f:
                        json.dump(save_data, f, ensure_ascii=False, indent=2)
                    self.status_label.setText("데이터 수집 완료 → 최신 데이터 사용 중")
                    break

                soup = BeautifulSoup(content, 'html.parser')
                rows = soup.select('tbody tr')

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        item = {
                            "부품그룹": cols[2].get_text(strip=True),
                            "부품번호": cols[3].get_text(strip=True),
                            "부품명": cols[4].get_text(strip=True),
                            "가격": cols[5].get_text(strip=True),
                            "적용일자": cols[6].get_text(strip=True),
                        }
                        collected.append(item)

                self.status_label.setText(f"수집 중... {page}페이지")
                page += 1
                time.sleep(self.DELAY)

            except Exception as e:
                self.log(f"[에러] {page} 페이지 수집 실패: {e}")
                break

    def search_data(self):
        keyword = self.search_input.text().strip().lower()
        if not keyword:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요!")
            return

        data_file_path = get_data_file_path(self.data_file)
        if not os.path.exists(data_file_path):
            QMessageBox.warning(self, "경고", "저장된 데이터가 없습니다. 데이터 수집을 먼저 진행해 주세요.")
            return

        with open(data_file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.loaded_data = saved_data.get("데이터", [])
        self.result_list.clear()
        count = 0
        for item in self.loaded_data:
            part_number = item.get("부품번호", "").lower()
            part_name = item.get("부품명", "").lower()
            if keyword in part_number or keyword in part_name:
                count += 1
                url = f"{self.BASE_URL}?sPL_CarModel={urllib.parse.quote(saved_data.get('차량'))}&sPL_PartsName={urllib.parse.quote(item.get('부품명'))}"
                self.result_list.addItem(f"부품그룹:{item.get('부품그룹')}| 부품번호:{item.get('부품번호')} | 부품명:{item.get('부품명')} | 가격:{item.get('가격')}원 | {url}")
        self.log(f"검색 완료: {count}건 찾음")

    def open_url(self, item):
        url = item.text().split("|")[-1].strip()
        webbrowser.open(url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

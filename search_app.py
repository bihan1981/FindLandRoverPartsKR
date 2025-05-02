import sys
import threading
import requests
import time
import webbrowser
import urllib3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QProgressBar, QListWidget, QTextEdit, QMessageBox
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MainWindow(QWidget):
    # 상수 값 (구성 파라미터)
    BASE_URL = "https://kr.landroverkorea.co.kr:6443/parts-info/parts_list.asp"
    MAX_PAGES = 200
    DELAY = 0.01

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FindLandRoverPartsKR")
        self.resize(700, 500)

        self.stop_event = threading.Event()
        self.found_pages = []

        self.init_ui()

    def init_ui(self):
        """UI 컴포넌트 초기화"""
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

        self.progress = QProgressBar()

        self.result_list = QListWidget()
        self.result_list.itemDoubleClicked.connect(self.open_url)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.result_list)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

    def log(self, message):
        """로그 출력"""
        self.log_output.append(message)

    def start_search(self):
        """검색 시작"""
        search_term = self.search_input.text().strip().lower()
        if not search_term:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요!")
            return

        # 초기화
        self.stop_event.clear()
        self.result_list.clear()
        self.log_output.clear()
        self.found_pages.clear()
        self.progress.setValue(0)

        self.log(f"🔍 '{search_term}' 검색 시작")

        # 검색 스레드 시작
        threading.Thread(target=self.search_thread, args=(search_term,), daemon=True).start()

    def stop_search(self):
        """검색 중단"""
        self.stop_event.set()
        self.log("🛑 검색 중단 요청됨")

    def search_thread(self, search_term):
        """검색 처리 로직 (별도 스레드)"""
        self.progress.setMaximum(self.MAX_PAGES)

        for page in range(1, self.MAX_PAGES + 1):
            if self.stop_event.is_set():
                self.log("검색 중단됨")
                break

            url = f"{self.BASE_URL}?intPage={page}&sPL_CarModel=DEFENDER%20(L663)&sPL_PartsGroup=Body%20-%20Trim&sPL_PartsName="

            try:
                resp = requests.get(url, verify=False, timeout=10)
                content = resp.text.lower()

                if search_term in content:
                    self.log(f"✅ {page} 페이지에서 발견")
                    self.result_list.addItem(f"{page}: {url}")
                    self.found_pages.append(url)
            except Exception as e:
                self.log(f"[에러] {page} 페이지 요청 실패: {e}")

            self.progress.setValue(page)
            time.sleep(self.DELAY)

        self.log("🔍 검색 완료")

    def open_url(self, item):
        """결과 항목 더블클릭 시 URL 열기"""
        url = item.text().split(": ", 1)[1]
        webbrowser.open(url)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

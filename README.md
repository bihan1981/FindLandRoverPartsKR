
# FindLandRoverPartsKR v2.0

A tool to search Land Rover Korea parts price by part number or name.  
(부품번호나 부품명으로 한국 랜드로버 부품 가격을 검색하는 툴)

---

## Features

- Vehicle selection → checks if stored data is up-to-date
- Admin-only **data collection** (requires PIN authentication)
- Local JSON data search → fast search without server crawling
- Search by part number or part name
- Shows search results with part number, part name, price
- Open original part page in browser by double-click
- Log output with status messages

---

## Requirements

- Python 3.8 or higher
- PyQt5
- requests
- beautifulsoup4
- urllib3

설치할 패키지는 `requirements.txt`에 포함되어 있습니다.

---

## Virtual Environment (Recommended)

It is recommended to use a **virtual environment** to avoid conflicts with global Python packages.

```bash
python -m venv venv
```

### Activate (Windows PowerShell)
```bash
venv\Scripts\Activate
```

### Activate (Windows CMD)
```bash
venv\Scriptsctivate.bat
```

### Activate (Mac/Linux)
```bash
source venv/bin/activate
```

---

## Installation

필요 모듈 설치:

```bash
pip install -r requirements.txt
```

---

## Usage

프로그램 실행:

```bash
python search_app.py
```

1. 프로그램을 실행합니다.
2. 차량을 선택하면 저장된 데이터의 최신 여부를 자동으로 확인합니다.
3. **최신 데이터가 없거나 업데이트 필요 시 → [데이터 수집] 버튼 활성화**
4. **[데이터 수집] 버튼 클릭 시 관리자용PIN 입력 → 올바른 PIN 입력 시 데이터 수집 시작**
5. 데이터 수집 완료 후 최신 데이터로 검색 가능
6. 검색어 입력 후 **[검색]** 버튼 클릭
7. 검색 결과 더블클릭 → 웹 브라우저로 원본 페이지 열람

⚠️ **일반 사용자는 데이터 수집이 필요 없습니다.(미리 받아두었습니다)** 

---

## Build (Windows executable)

Windows에서 단일 실행파일(`.exe`)로 빌드하려면:

```bash
pyinstaller --onefile --windowed --icon=landrover_tad_icon.ico --add-data "options.json;." --add-data "data;data" search_app.py
```

- `--onefile`: 단일 exe 생성
- `--windowed`: 콘솔창 숨김
- `--icon`: 앱 아이콘 지정 (선택사항)
- `--add-data "data;data"`: `data` 폴더 전체 포함
- `--add-data "options.json;."`: options.json 포함

빌드 후 `dist/` 폴더에 `search_app.exe`가 생성됩니다.

---

## Screenshot

![part number](screenshot.jpg)
![part name](screenshot_partname.jpg)

---

## License

This project is licensed under the MIT License.  
자유롭게 사용, 수정, 배포 가능합니다.


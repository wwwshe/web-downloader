# Web Downloader

웹페이지에 포함된 다운로드 링크를 검색하고, 링크에 표시된 텍스트를 파일명으로 저장하는 Windows GUI 프로그램입니다.

<img width="300" height="200" alt="스크린샷 2026-10-12 011514" src="https://github.com/user-attachments/assets/e99f9ef1-7667-48a9-b32d-9d7878a16659" />


## 주요 기능

- 웹페이지 URL에서 다운로드 링크 검색
- 확장자별 필터링 (예: `zip`, `pdf`, `egg`)
- 전체 다운로드 및 선택 다운로드
- 저장 폴더 지정 및 설정 저장
- 기존 파일 건너뛰기, 다운로드 결과 로그 확인

## 실행 방법 (일반 사용자)

배포된 `web-downloader.exe`를 더블 클릭하면 됩니다. **Python을 별도로 설치할 필요가 없습니다.**

설정은 실행 파일과 같은 폴더의 `downloader_settings.json`에 저장됩니다. 설정을 저장하려면 해당 폴더에 쓰기 권한이 있어야 합니다.

## 사용 방법

1. **웹페이지 URL**을 입력합니다.
2. 필요한 경우 **확장자**를 입력합니다. 비워두면 확장자 필터 없이 검색합니다.
3. **저장 폴더**를 지정하고 **링크 검색**을 누릅니다.
4. 검색 결과에서 **전체 다운로드** 또는 **선택 다운로드**를 누릅니다.
5. 하단 로그에서 다운로드 결과를 확인합니다.

## EXE 빌드 (개발자)

Windows에서 Python 3 및 `pip`이 설치되어 있어야 합니다. `build_exe.bat`을 더블 클릭하면 필요한 패키지를 설치하고 PyInstaller로 실행 파일을 빌드합니다.

빌드 결과는 `dist\web-downloader.exe`입니다.

직접 명령어로 빌드하려면 다음을 실행하세요.

```bat
python -m pip install pyinstaller requests beautifulsoup4
python -m PyInstaller --noconfirm --clean --onefile --windowed --name web-downloader downloader_gui_exe.py
```

소스 코드를 직접 실행하려면 다음을 사용하세요.

```bat
python -m pip install requests beautifulsoup4
python downloader_gui_exe.py
```

## 파일 구성

| 파일 | 설명 |
| --- | --- |
| `downloader_gui_exe.py` | GUI 및 다운로드 기능을 구현한 Python 소스 |
| `build_exe.bat` | Windows EXE 자동 빌드 스크립트 |
| `dist/web-downloader.exe` | 빌드 후 생성되는 배포용 실행 파일 |
| `downloader_settings.json` | 실행 시 생성되는 사용자 설정 파일 |

## 참고 사항

- 검색 대상은 HTML의 `<a href>` 링크이며, 링크에 표시된 텍스트를 파일명으로 사용합니다.
- 확장자 필터는 실제 다운로드 URL이 아닌 **링크 텍스트**를 기준으로 적용됩니다.
- 로그인이나 JavaScript 실행이 필요한 페이지에서는 링크를 찾지 못할 수 있습니다.
- 같은 이름의 파일이 이미 있으면 덮어쓰지 않고 건너뜁니다.
- EXE는 Windows에서 빌드해야 하며, 일부 PC에서는 보안 소프트웨어가 처음 실행하는 파일을 검사할 수 있습니다.

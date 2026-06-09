# Key Macro Studio

Windows와 macOS에서 사용할 수 있는 키보드 매크로 데스크톱 앱입니다.

시각적 키보드에서 키를 누르듯이 매크로 순서를 만들고, 각 키마다 `클릭`, `N초 유지`, `누른 상태 유지`, `떼기`, `대기` 같은 동작을 설정할 수 있습니다. 실행 버튼을 누르면 설정한 대기시간 뒤에 현재 최상단에 있는 앱으로 키 입력을 보냅니다.

## 주요 기능

- 키별 유지시간 설정
  - 예: 오른쪽 방향키 0.05초 클릭
  - 예: Shift 5초 유지
  - 예: Ctrl 누른 상태 유지 후 나중에 떼기
- 전체 실행시간 설정
  - 예: 매크로 전체를 30초 동안 반복 실행
- 실행 전 대기시간 설정
  - 기본값은 5초
- 긴급 중지 키
  - 기본값은 F12
- 시각적 키보드 + 리스트 편집기
- 프로필 저장
- JSON 가져오기/내보내기

## 설치 준비

Python 3.10 이상이 필요합니다.

현재 PC에 Python이 설치되어 있는지 확인합니다.

```powershell
python --version
```

## Windows 실행 방법

PowerShell에서 프로젝트 폴더로 이동합니다.

```powershell
cd "C:\Users\testuser123\Documents\New project\key-macro-studio"
```

가상환경을 만들고 활성화합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

필요한 패키지를 설치합니다.

```powershell
python -m pip install -r requirements.txt
```

앱을 실행합니다.

```powershell
python -m key_macro_studio
```

## macOS 실행 방법

터미널에서 프로젝트 폴더로 이동합니다.

```bash
cd "/path/to/key-macro-studio"
```

가상환경을 만들고 활성화합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

필요한 패키지를 설치합니다.

```bash
python -m pip install -r requirements.txt
```

앱을 실행합니다.

```bash
python -m key_macro_studio
```

macOS에서는 키보드 입력 자동화를 위해 권한 허용이 필요할 수 있습니다.

`시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용`에서 터미널 또는 패키징된 앱을 허용하세요. 필요하면 `입력 모니터링` 권한도 허용합니다.

## 사용 방법

1. 시각적 키보드에서 원하는 키를 클릭합니다.
2. 아래 리스트에서 각 키의 동작을 수정합니다.
   - `클릭`: 짧게 누르고 뗍니다.
   - `유지`: 지정한 시간(ms) 동안 누르고 뗍니다.
   - `누른 상태 유지`: 키를 계속 누른 상태로 둡니다.
   - `떼기`: 이전에 누른 키를 뗍니다.
   - `대기`: 키 입력 없이 기다립니다.
   - `반복`: 반복 동작에 사용할 수 있는 타입입니다.
3. 시작 전 대기시간을 설정합니다.
   - 기본값은 5초입니다.
4. 전체 실행시간을 설정합니다.
   - `30`이면 30초 동안 매크로를 반복합니다.
   - `0`이면 매크로를 1회만 실행합니다.
5. `실행` 버튼을 누릅니다.
6. 대기시간 안에 조작할 앱을 최상단으로 올립니다.
7. 중지하려면 F12를 누르거나 앱의 `중지` 버튼을 누릅니다.

## 예시 매크로

오른쪽 방향키를 한 번 누르고, Shift를 5초 유지하고, Ctrl을 누른 상태에서 Space를 1초 누른 뒤 Ctrl을 떼고, 왼쪽 방향키를 한 번 누르는 예시입니다.

```json
{
  "name": "sample macro",
  "startupDelaySeconds": 5,
  "totalDurationSeconds": 30,
  "stopHotkey": "F12",
  "steps": [
    { "key": "right", "action": "tap", "durationMs": 50 },
    { "key": "shift", "action": "press_for", "durationMs": 5000 },
    { "key": "ctrl", "action": "key_down" },
    { "key": "space", "action": "press_for", "durationMs": 1000 },
    { "key": "ctrl", "action": "key_up" },
    { "key": "left", "action": "tap", "durationMs": 50 }
  ]
}
```

## 테스트 실행

핵심 매크로 엔진 테스트는 GUI 패키지 없이도 실행할 수 있습니다.

```powershell
cd "C:\Users\testuser123\Documents\New project\key-macro-studio"
$env:PYTHONPATH="C:\Users\testuser123\Documents\New project\key-macro-studio\src"
python -m unittest discover -s tests
```

macOS/Linux에서는 다음처럼 실행합니다.

```bash
cd "/path/to/key-macro-studio"
PYTHONPATH=src python -m unittest discover -s tests
```

## 실행 파일로 만들기

PyInstaller로 실행 파일을 만들 수 있습니다.

```powershell
python -m pip install pyinstaller
pyinstaller --noconsole --name KeyMacroStudio --collect-all PySide6 -m key_macro_studio
```

빌드 결과는 `dist/KeyMacroStudio` 폴더에 생성됩니다.

## 주의사항

- 실행 버튼을 누른 뒤 대기시간 동안 조작할 앱을 최상단으로 올려야 합니다.
- Windows에서 대상 앱이 관리자 권한으로 실행 중이면 Key Macro Studio도 관리자 권한으로 실행해야 키 입력이 전달될 수 있습니다.
- macOS에서는 손쉬운 사용 권한이 없으면 키 입력 자동화가 차단될 수 있습니다.
- F12 중지 시 앱이 누르고 있던 키는 모두 자동으로 해제됩니다.

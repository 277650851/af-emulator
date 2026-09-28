# Assault Fire Server Emulator

**언어:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [다른 언어](README-LANGUAGES.md)

**Assault Fire PH** 보존과 서버 에뮬레이션을 위한 비공식 프로젝트입니다. 이 프로젝트와 제3자가 운영하는 서버는 Tencent, Level Up! Games 또는 원래 권리자와 제휴·후원·승인 관계가 없습니다. 커뮤니티 서버는 독립적으로 운영됩니다.

> **지원 및 테스트된 버전:** Assault Fire PH **v1.0.0.24만** 지원합니다. 이 저장소에는 게임 파일이 포함되어 있지 않습니다. 게임 파일은 직접 보유해야 합니다.

## 가장 쉬운 시작 방법

1. `af-emulator` 폴더 전체를 Assault Fire PH 게임 폴더 안에 넣습니다.
2. `START_ASSAULT_FIRE.ps1`을 마우스 오른쪽 버튼으로 클릭하고 **Run with PowerShell**을 선택합니다. Windows에서 관리자 권한을 요청하면 허용합니다.
3. 실행 스크립트가 버전과 설정을 확인하고 로컬 키를 준비한 뒤 서버, 실행 도우미, 게임 클라이언트를 시작합니다.
4. 클라이언트에 로그인합니다. **START** 버튼이 나타나면 눌러 계속합니다.

일반 원클릭 방식에서는 서버나 패치 도구를 직접 실행할 필요가 없습니다. 스크립트는 게임을 다운로드하거나 배포하지 않고 사용자의 로컬 파일만 사용합니다. 버전이 다르거나 `TGame.exe` 또는 `TCLS.dll` 서명을 확인할 수 없으면 중단하고 패치를 강제로 적용하지 마세요. 게임을 시작하기 전에 런처는 검증된 날짜/시간 패치를 `TGame.exe`에 영구 적용하고, 먼저 바이트 단위로 동일한 `TGame.exe.bak` 백업을 만듭니다. 서명이나 안전한 코드 영역을 확인하지 못하면 파일을 수정하지 않습니다.

## 수동 설정 및 개발자 안내

전체 절차와 정확한 명령은 [영문 전체 안내서](README.md)를 참고하세요. Windows, Python 3.10 이상, 지원되는 게임 버전의 본인 소유 파일이 필요합니다. 수동 설정에서는 사전 점검이 `UNLOCKED`가 될 때까지 기다리세요. 수동 실행 중에는 도우미가 `TCLS ARMED`를 표시하기 전에 **START**를 누르지 마세요. `--server-only`는 서버 호스팅용이며 로컬 게임 실행을 허용하지 않습니다.

## 상태 및 도움 요청

현재 공개 안정 기준은 **v143b**입니다. VERSION, AUTH, DIR, ROLE, ZONE 흐름과 방 관리, PvE 매치 흐름이 작동합니다. 최초 닉네임/계정 생성 및 일부 소셜/진행 기능은 아직 개발 중입니다. 클라이언트의 초기 AP 동기화는 임시 로컬 방식을 사용합니다.

도움을 요청할 때 오류 화면, 진행 중이던 단계, 실행한 정확한 명령, `server/af_server_live.log`, 게임 버전을 보내 주세요. `PRIVATE.PEM`, 비밀번호, 계정 정보, 토큰, 원본 게임 파일은 **보내지 마세요**.

- [프로젝트 상태](docs/STATUS.md) · [런처 오류](docs/LAUNCHER_ERRORS.md) · [중요 설정 참고](docs/VITAL_SETUP_NOTES.md) · [문서 목차](docs/README.md)
- [언어별 README 전체 목록](README-LANGUAGES.md)

**라이선스:** MIT.

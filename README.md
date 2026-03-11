# UBT Coding Partner (Python GUI)

언리얼 빌드 툴(UBT) 실행/로그 분석/세션 브랜칭/파일 변경 추적을 한 번에 처리하는 로컬 GUI 도구입니다.

## 핵심 기능

- 로컬 저장소 파일 변경사항 자동 추적(업로드 없이 로컬 읽기)
- UBT 빌드 옵션 클릭 실행 + 로그 저장 + 에러 요약
- 다양한 AI API 제공자 등록/선택
- 세션/브랜치(멀티버스) 구조로 진행 상태 보관
- 코드 참조 맵(파일 간 include/import 관계) 생성 및 세션별 보관
- 변경 파일/최근 로그/세션 메타를 하나의 워크스페이스에 기록

## 빠른 시작

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install requests
python app.py
```

> `requests`는 외부 AI API 호출 시에만 필요합니다. 오프라인 사용은 설치 없이도 대부분 동작합니다.

## 기본 사용 흐름

1. GUI에서 `Repo Path`를 지정하고 **Start Tracking**.
2. `UBT` 탭에서 타깃/플랫폼/설정 입력 후 **Run Build**.
3. 로그/에러 요약 확인, 필요 시 **Save Snapshot**으로 세션 스냅샷 저장.
4. **Create Branch Session**으로 현재 세션에서 분기(멀티버스) 생성.
5. `Reference Map` 탭에서 코드 참조 그래프 재생성.

## 디렉터리

앱 실행 시 아래 구조가 자동 생성됩니다.

- `.ubt_partner/sessions/*.json` : 세션/브랜치 데이터
- `.ubt_partner/logs/*.log` : 빌드 로그 원본
- `.ubt_partner/config/providers.json` : AI API 제공자 설정


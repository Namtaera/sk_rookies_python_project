## 📌 협업 규칙

### 1. Git 사용 규칙

- main 브랜치에 직접 개발하지 말고 각자 브랜치 생성 후 작업하기
- 작업 완료 후 Pull Request(PR) 생성 후 merge

---

### 2. 환경 변수 관리

- API Key 등 민감 정보는 절대 GitHub에 업로드 금지
- .env 파일 사용 (gitignore에 포함)
- .env 파일은 팀 카톡방으로 공유

---

### 3. 실행 테스트

- PR 전에 반드시 실행 테스트 확인
- 오류 없는 상태에서 merge 진행

---

### 4. 코드 충돌 방지

- 작업 전 항상 pull 받아 최신 상태 유지
- 작업 후 바로 push 하지 말고 변경사항 확인

---



### 5. 프로젝트 디렉터리 구조

```
project/
├── main.py  또는  app.py     ← Flask 진입점
├── config.py                 ← API 키 모음()
│
├── api/                      ← 1팀
│   ├── geocoder.py
│   └── opinet.py
│
├── utils/                    ← 2팀 (1번 역할)
│   ├── validator.py
│   └── report.py             ← CSV/JSON (1팀)
│
└── templates/                ← 2팀 (2번, 3번 역할)
    ├── index.html            ← 주소 입력 페이지
    └── result.html           ← 결과 출력 페이지
```

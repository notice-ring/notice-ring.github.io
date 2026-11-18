# Jihwan Gong — personal homepage

영어가 기본인 한·영 개인 홈페이지. 한국어 페이지는 `/kr/` 아래에 있습니다. Python 3 표준 라이브러리만 사용하며, 배포 결과물에는 JavaScript나 별도 런타임이 필요하지 않습니다.

## 빌드

```sh
cd /Users/gong/Desktop/me/homepage
python3 build.py
python3 -m unittest discover -s tests
```

`dist/index.html`을 직접 열어볼 수 있습니다.

## GitHub Pages 배포

- 주소: https://notice-ring.github.io/
- 저장소: https://github.com/notice-ring/notice-ring.github.io/tree/homepage
- 배포 소스: `homepage` 브랜치의 `/docs`
- 기존 Jekyll 테마는 `master` 브랜치에 보존합니다.

이 폴더에서 내용을 수정한 후 아래 명령으로 배포합니다.

```sh
python3 -m unittest discover -s tests
python3 build.py --output docs
git add build.py content templates static tests docs README.md .gitignore
git commit -m "Update personal homepage"
git push origin homepage
```

GitHub Pages가 `docs/`의 변경을 자동 배포합니다. 기본 로컬 미리보기 `dist/`와 공개용 `docs/`는 같은 템플릿과 글 데이터로 생성합니다. `docs/`를 직접 수정하지 않습니다.

## 수정 위치

- 소개: `templates/index.html`
- 메뉴와 공통 레이아웃: `templates/layout.html`, `build.py`
- 연구·동아리: `templates/research.html`, `templates/community.html`
- 한국어 페이지 문구: `templates/kr/`의 대응 템플릿
- 프로필 사진: `static/assets/jihwan-gong.png`
- 디자인과 반응형 레이아웃: `static/styles.css`
- CV: `static/assets/Jihwan_Gong_CV.pdf`
- Note 목록과 본문: `content/notes.json` (`notes.html` 목록과 `note/<slug>.html` 글로 생성)

수정 후 `python3 build.py`를 실행합니다. `dist/`를 직접 고치면 다음 빌드 때 덮어씁니다.

## Note 추가

현재는 Note 목록 페이지에 공개된 게시물이 없습니다. `content/notes.json`의 배열에 아래와 같은 객체를 추가합니다. 예시는 설명용이며 실제 게시물로 넣지 않았습니다.

```json
[
  {
    "slug": "my-first-note",
    "title": "첫 글 제목",
    "date": "2026-11-16",
    "language": "ko",
    "summary": "목록에 보일 짧은 소개",
    "body": ["첫 번째 문단", "두 번째 문단"],
    "draft": true,
    "category": null
  }
]
```

`draft: true`인 글은 목록과 페이지 모두 생성하지 않습니다. 공개할 때 `false`로 바꿉니다. 두 언어의 목록에 최신 날짜순으로 표시되며, 개별 글은 원문으로 제공됩니다. 개별 주소는 `note/my-first-note.html`입니다. 삭제하거나 초안으로 돌린 글의 기존 출력 페이지도 다음 빌드에서 제거됩니다. `language`는 `en` 또는 `ko`이며 생략하면 `en`입니다. 제목과 본문은 HTML이 아닌 일반 텍스트입니다.

`category`는 생략하거나 `null`로 둘 수 있고, 현재 화면에는 표시하지 않습니다. 분류가 정해지면 데이터 구조를 바꾸지 않고 목록 필터를 추가할 수 있습니다. 본문에 코드 블록이나 그림이 자주 필요해질 때 Markdown 지원을 추가하면 됩니다.

## 공개 범위

빌더는 `static/`과 위 템플릿·글 데이터만 사용합니다. 상위 작업 폴더나 `private/`, 원본 자료 폴더를 배포 대상으로 삼지 않습니다.

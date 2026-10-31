# 🎬 자동 릴스 메이커 (Reels Maker)

주제 한 줄만 넣으면 **대본 → 내레이션 음성 → 배경 이미지 → 배경음악 → 자막**까지
전부 자동으로 만들어 주는 세로형(9:16) 스토리 영상 제작기입니다.

> 예: `"슬프고 아름다운 실화"` + `5분` → 5분짜리 감성 내레이션 영상 완성

---

## ✨ 무엇을 자동으로 해주나요?

| 단계 | 하는 일 | 사용하는 것 (무료/유료) |
|---|---|---|
| 1. 대본 | 실화 기반 스토리를 장면별로 작성, 캡션·해시태그·출처까지 | Claude API (유료, 영상 1개당 약 몇백 원 수준) |
| 2. 음성 | 문장마다 자연스러운 AI 내레이션 | Microsoft Edge 음성 (무료) |
| 3. 배경 | 장면 분위기에 맞는 사진 + 천천히 줌인/줌아웃 | 내 사진 / Pexels 무료 사진 / 자동 생성 배경 |
| 4. 음악 | 잔잔한 피아노 BGM 자동 작곡, 말할 때는 음악이 자동으로 작아짐 | 직접 생성 (저작권 걱정 없음) |
| 5. 영상 | 1080×1920 MP4, 자막·제목 삽입, 커버 이미지, 캡션 파일 | ffmpeg |

결과물 (`output/날짜_제목/` 폴더):
- `reel.mp4` – 완성 영상
- `reel_part1.mp4`, `reel_part2.mp4` … – `--split` 사용 시 나눠진 영상
- `cover.jpg` – 릴스 커버(썸네일)
- `caption.txt` – 바로 붙여넣는 게시글 문구 + 해시태그 + 출처
- `story.json` – 대본 (고쳐서 다시 만들 수 있음)

---

## 📱 방법 A — 휴대폰으로 사용하기 (GitHub Actions, 설치 필요 없음)

**처음 한 번만 설정:**
1. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
2. `ANTHROPIC_API_KEY` 추가 (https://console.anthropic.com 에서 발급, 블로그 자동화에 쓰던 키와 같은 것 사용 가능)
3. (선택) `PEXELS_API_KEY` 추가 — https://www.pexels.com/api/ 에서 무료 발급. 넣으면 실제 사진 배경을 사용합니다.

**영상 만들 때마다:**
1. 저장소 → **Actions** 탭 → **Make story reel** → **Run workflow**
2. 주제, 길이(분), 언어, 목소리 입력 → 초록색 **Run workflow** 버튼
3. 10~20분 후 완료되면 실행 기록 맨 아래 **Artifacts** 에서 zip 다운로드 → 영상 확인

> 자동으로 주 2회 영상을 만들고 싶다면 `.github/workflows/make-reel.yml` 의 `schedule` 부분 주석(#)을 지우세요.

---

## 💻 방법 B — 내 컴퓨터에서 사용하기

```bash
# 1) 준비 (처음 한 번)
#    - Python 3.10 이상, ffmpeg 설치 (Mac: brew install ffmpeg / Windows: winget install ffmpeg)
cd reels-maker
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
export PEXELS_API_KEY=...                # 선택

# 2) 영상 만들기
python make_reel.py --topic "슬프고 아름다운 실화" --minutes 5
```

### 자주 쓰는 예시

```bash
# API 키 없이 샘플 대본(충견 하치코 실화)으로 바로 만들어 보기
python make_reel.py --story samples/hachiko_ko.json

# 남자 목소리, 조금 더 느리게
python make_reel.py --topic "전쟁 속에서 지켜낸 사랑 실화" --voice ko-male --rate -15%

# 일본어 영상
python make_reel.py --topic "悲しくて美しい実話" --lang ja --voice ja-female

# 내 사진 + 내 음악으로
python make_reel.py --topic "돌고래가 사람을 구한 실화" --images ./my_photos --music ./bgm.mp3

# 5분 영상 + 릴스용 90초 파트로도 자르기
python make_reel.py --topic "감동적인 가족 실화" --minutes 5 --split 90

# 대본(story.json)을 직접 고친 뒤 다시 만들기
python make_reel.py --story output/20261031_1800_제목/story.json

# 소리 없이 화면만 빠르게 미리보기 (인터넷 없이도 가능)
python make_reel.py --story samples/hachiko_ko.json --tts none
```

### 전체 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--topic` | 이야기 주제 (Claude가 대본 작성) | – |
| `--story` | 이미 있는 대본 JSON 사용 | – |
| `--minutes` | 목표 길이(분) | 5 |
| `--lang` | `ko` / `ja` / `en` | ko |
| `--voice` | `ko-female`, `ko-male`, `ja-female`, `ja-male`, `en-female`, `en-male` | 언어별 여성 |
| `--rate` | 말하기 속도 (`-15%` 느리게, `+5%` 빠르게) | -8% |
| `--images` | 내 사진 폴더 (파일 이름 순서대로 사용) | – |
| `--music` | 내 배경음악 파일 | 자동 작곡 |
| `--music-mood` | `sad` (슬픈) / `warm` (따뜻한) | sad |
| `--music-volume` | 배경음악 크기 0~1 | 0.22 |
| `--split` | N초 단위로 파트 나누기 (0 = 안 나눔) | 0 |
| `--tts` | `edge` (실제 음성) / `none` (무음 미리보기) | edge |

---

## ⚠️ 꼭 알아두세요

1. **영상 길이 제한** — 인스타그램 릴스는 업로드 길이 제한이 있습니다(현재 최대 약 3분, 정책은 수시로 바뀜).
   5분 영상은 **유튜브 / 페이스북 일반 영상**에 올리고, 릴스·쇼츠에는 `--split 90` 으로 나눈 파트를
   "1편, 2편…" 시리즈로 올리는 방법을 추천합니다. (시리즈는 팔로우 유도에도 효과적입니다.)
2. **"실화"의 정확성** — Claude에게 "널리 기록된 진짜 이야기만, 사실을 지어내지 말 것"을 지시하고
   `caption.txt` 에 출처를 함께 적도록 했습니다. 그래도 AI는 실수할 수 있으니, **올리기 전에 출처를 한 번 확인**해 주세요.
3. **저작권** — 배경음악은 프로그램이 직접 만든 것이라 안전합니다. Pexels 사진도 상업적 이용이 무료입니다.
   직접 음악을 넣을 때는 사용 허가가 있는 음원만 쓰세요.
4. **AI 음성 표시** — 인스타그램/유튜브는 AI 생성 콘텐츠 표시(라벨)를 권장합니다. 업로드할 때 "AI 정보" 옵션을 켜 두면 안전합니다.

## 🛠 구조 (개발자용)

```
reels-maker/
├── make_reel.py          # 실행 파일 (전체 흐름)
├── reelmaker/
│   ├── story.py          # 1. Claude 대본 생성
│   ├── voice.py          # 2. 문장별 TTS
│   ├── visuals.py        # 3. 배경 이미지
│   ├── music.py          # 4. BGM 작곡 / 루프
│   ├── render.py         # 5. 타임라인 · 자막(ASS) · 줌 효과 · 합성
│   └── config.py         # 화면 크기, 폰트, 목소리, 색감 설정
└── samples/hachiko_ko.json
```

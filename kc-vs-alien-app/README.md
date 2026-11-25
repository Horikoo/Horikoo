# KC vs Alien — 앱 출시 가이드 (App publishing guide)

이 폴더는 **KC vs Alien** 게임을 안드로이드/아이폰 앱으로 만든 프로젝트입니다.
(This folder turns the KC vs Alien web game into Android and iPhone apps with Capacitor.)

| 항목 | 값 |
|---|---|
| 앱 이름 | KC vs Alien |
| 앱 ID (패키지 이름) | `com.kcvsalien.game` — **출시 후에는 절대 바꿀 수 없음** |
| 게임 코드 | `www/index.html` |
| 스토어용 이미지·문구 | `store/` 폴더 |
| 안드로이드 빌드 | GitHub Actions가 클라우드에서 자동으로 빌드 |

---

## 🤖 안드로이드 (Google Play) — 추천: 먼저 이것부터

비용: **$25 (한 번만)**. 컴퓨터에 아무것도 설치할 필요 없습니다.

### 1단계. 서명 키를 GitHub에 등록 (한 번만)
Claude가 만들어 준 `kc-vs-alien-signing-key` 폴더 안의 `GITHUB-SECRETS-README.txt`를 여세요.
1. GitHub에서 이 저장소 → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** 버튼으로 4개를 추가:
   `KC_KEYSTORE_BASE64`, `KC_KEYSTORE_PASSWORD`, `KC_KEY_ALIAS`, `KC_KEY_PASSWORD`
3. ⚠️ 그 키 폴더는 USB와 클라우드 두 곳에 백업하세요. 잃어버리면 업데이트가 매우 어려워집니다.

### 2단계. 앱 파일 받기
1. GitHub 저장소 → **Actions** 탭 → **KC vs Alien Android build**
2. 오른쪽 **Run workflow** 버튼 클릭 (또는 코드를 올리면 자동 실행)
3. 약 5~10분 후 초록색 ✅이 뜨면 클릭 → 맨 아래 **Artifacts**에서 다운로드:
   - `kc-vs-alien-test-apk` → 내 폰에 바로 설치해서 테스트용
   - `kc-vs-alien-play-store-aab` → **구글 플레이에 올리는 파일** (1단계를 해야 생김)

### 3단계. Google Play Console에 올리기
1. https://play.google.com/console 에서 개발자 계정 생성 ($25, 신분증 인증 필요)
2. **앱 만들기** → 이름 `KC vs Alien`, 게임, 무료
3. **스토어 등록정보**: `store/store-listing.md`의 문구를 복사, 이미지 업로드
   - 앱 아이콘: `store/icon-512.png`
   - 그래픽 이미지: `store/feature-graphic-1024x500.png`
   - 휴대전화 스크린샷: `store/screenshot-1-title.png`, `-2-action.png`, `-3-boss.png`
4. **개인정보처리방침 URL**: `store/privacy-policy.html`을 인터넷에 공개된 주소로 올린 뒤 그 주소를 입력
5. **데이터 보안**: "수집하는 데이터 없음" (`store-listing.md` 맨 아래 참고)
6. **콘텐츠 등급** 설문 작성 → 폭력: 만화 같은 우주선 전투
7. **테스트 → 비공개 테스트**에 `.aab` 업로드
   - ⚠️ 2023년 11월 이후 만든 **개인** 개발자 계정은, 정식 출시 전에 **테스터 12명이 14일 동안** 비공개 테스트를 해야 합니다. 가족·친구에게 부탁하세요.
8. 14일 후 **프로덕션**으로 출시 신청 → 구글 검토 (보통 며칠)

### 업데이트할 때
게임을 고치고 코드를 올리면 GitHub이 새 `.aab`를 자동으로 만듭니다. 버전 번호도 자동으로 올라갑니다.

---

## 🍎 아이폰 (App Store)

아이폰 프로젝트(`ios/` 폴더)도 준비되어 있지만, 애플은 **Mac 컴퓨터 + Xcode**가 꼭 필요합니다.
- 비용: **$99 / 년** (Apple Developer Program)
- Mac에서: `npm install` → `npx cap open ios` → Xcode에서 팀 선택 → **Product → Archive** → 업로드
- Mac이 없다면 나중에 클라우드 Mac 빌드 서비스(예: Codemagic, Ionic Appflow)를 쓰는 방법도 있습니다.

---

## 🔧 개발자용 메모 (For developers)

```bash
npm install            # 패키지 설치
npx cap sync           # www/ 게임을 android/, ios/ 프로젝트로 복사
npm run icons          # assets/ 이미지로 아이콘·스플래시 재생성
npx cap open android   # Android Studio에서 열기
```

- 게임을 고칠 땐 `www/index.html`을 수정한 뒤 `npx cap sync`.
- 글꼴(Russo One, Chakra Petch)은 SIL Open Font License로, 앱 안에 포함해도 됩니다 (`www/fonts/OFL-*.txt`).
- 서명 키(`.jks`)는 절대 이 저장소에 커밋하지 마세요.

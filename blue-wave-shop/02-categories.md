# Blue Wave Shop 카테고리와 메뉴 구성

고객이 원하는 옷을 **3번 클릭 안에** 찾을 수 있도록 만든 구조입니다.
Shopify에서는 카테고리를 **컬렉션(Collection)** 이라고 부릅니다.

---

## 1. 전체 메뉴 구조 (한눈에 보기)

```
Blue Wave Shop
├── 신상품 (New)
├── 여성 (Women)
│   ├── 상의 · 하의 · 원피스 · 아우터 · 니트
├── 남성 (Men)
│   ├── 티셔츠 · 셔츠 · 바지 · 아우터 · 정장
├── 비치웨어 (Beach)
│   ├── 수영복 · 래시가드 · 비치셔츠 · 반바지
├── 운동복 (Active)
│   ├── 트레이닝복 · 레깅스 · 격투기·헬스웨어
├── 작업복 (Work)
│   ├── 작업 바지 · 안전 조끼 · 작업 셔츠
├── 잡화 (Accessories)
│   ├── 모자 · 가방 · 양말 · 선글라스
└── 세일 (Sale)
```

---

## 2. 컬렉션 목록 (3개 국어 이름 + 주소)

**핸들(handle)** 은 웹 주소 끝부분입니다. 예: `bluewaveshop.com/collections/women-tops`
핸들은 영어 소문자와 하이픈(-)만 쓰고, 한 번 정하면 바꾸지 않는 게 좋아요.

### 대분류

| 한국어 | English | 日本語 | 핸들 |
|---|---|---|---|
| 신상품 | New Arrivals | 新着 | `new` |
| 여성 | Women | レディース | `women` |
| 남성 | Men | メンズ | `men` |
| 비치웨어 | Beachwear | ビーチウェア | `beach` |
| 운동복 | Activewear | スポーツウェア | `active` |
| 작업복 | Workwear | ワークウェア | `work` |
| 잡화 | Accessories | 小物 | `accessories` |
| 세일 | Sale | セール | `sale` |

### 소분류

| 대분류 | 한국어 | English | 日本語 | 핸들 |
|---|---|---|---|---|
| 여성 | 상의 | Tops | トップス | `women-tops` |
| 여성 | 하의 | Bottoms | ボトムス | `women-bottoms` |
| 여성 | 원피스 | Dresses | ワンピース | `women-dresses` |
| 여성 | 아우터 | Outerwear | アウター | `women-outerwear` |
| 여성 | 니트 | Knitwear | ニット | `women-knitwear` |
| 남성 | 티셔츠 | T-Shirts | Tシャツ | `men-tshirts` |
| 남성 | 셔츠 | Shirts | シャツ | `men-shirts` |
| 남성 | 바지 | Pants | パンツ | `men-pants` |
| 남성 | 아우터 | Outerwear | アウター | `men-outerwear` |
| 남성 | 정장 | Suits | スーツ | `men-suits` |
| 비치웨어 | 수영복 | Swimwear | 水着 | `beach-swimwear` |
| 비치웨어 | 래시가드 | Rash Guards | ラッシュガード | `beach-rashguards` |
| 비치웨어 | 비치셔츠 | Beach Shirts | ビーチシャツ | `beach-shirts` |
| 비치웨어 | 반바지 | Board Shorts | ボードショーツ | `beach-shorts` |
| 운동복 | 트레이닝복 | Tracksuits | トレーニングウェア | `active-tracksuits` |
| 운동복 | 레깅스 | Leggings | レギンス | `active-leggings` |
| 운동복 | 격투기·헬스웨어 | Fight & Gym | 格闘技・ジムウェア | `active-fight-gym` |
| 작업복 | 작업 바지 | Work Pants | ワークパンツ | `work-pants` |
| 작업복 | 안전 조끼 | Safety Vests | 安全ベスト | `work-safety-vests` |
| 작업복 | 작업 셔츠 | Work Shirts | ワークシャツ | `work-shirts` |
| 잡화 | 모자 | Hats | 帽子 | `acc-hats` |
| 잡화 | 가방 | Bags | バッグ | `acc-bags` |
| 잡화 | 양말 | Socks | 靴下 | `acc-socks` |
| 잡화 | 선글라스 | Sunglasses | サングラス | `acc-sunglasses` |

---

## 3. 태그 규칙 (자동 분류의 핵심)

상품마다 **태그**를 붙여두면, 컬렉션에 상품이 **자동으로** 들어갑니다.
상품을 하나씩 컬렉션에 넣을 필요가 없어져서 시간이 크게 줄어요.

| 태그 종류 | 형식 | 예시 |
|---|---|---|
| 성별 | `gender:값` | `gender:women`, `gender:men`, `gender:unisex` |
| 라인 | `line:값` | `line:beach`, `line:active`, `line:work` |
| 소분류 | 소분류 핸들 그대로 | `women-tops`, `work-pants` |
| 세일 | `sale` | `sale` |
| 신상품 | `new` | `new` |

**예시: 남성용 래시가드 (세일 중)**
태그 → `gender:men`, `line:beach`, `beach-rashguards`, `sale`

> 팁: 남녀 공용 상품은 `gender:unisex` 태그를 붙이고, 여성·남성 컬렉션 조건에
> `gender:unisex`도 함께 넣으면 양쪽에 모두 보입니다.

---

## 4. 자동 컬렉션 조건

컬렉션을 만들 때 **"자동"** 을 고르고 아래 조건을 넣으세요.

| 컬렉션 | 조건 | 일치 방식 |
|---|---|---|
| 신상품 `new` | 상품 태그 = `new` | - |
| 여성 `women` | 태그 = `gender:women` **또는** 태그 = `gender:unisex` | 아무 조건이나 |
| 남성 `men` | 태그 = `gender:men` **또는** 태그 = `gender:unisex` | 아무 조건이나 |
| 비치웨어 `beach` | 태그 = `line:beach` | - |
| 운동복 `active` | 태그 = `line:active` | - |
| 작업복 `work` | 태그 = `line:work` | - |
| 세일 `sale` | 태그 = `sale` | - |
| 소분류 (예: `women-tops`) | 태그 = `women-tops` | - |

> 세일 컬렉션은 "비교 가격(compare at price)이 0보다 큼" 조건으로 만들어도 됩니다.
> 그러면 할인 가격을 입력하는 순간 자동으로 세일 메뉴에 들어갑니다.

---

## 5. Shopify에 등록하는 순서

### 1단계: 컬렉션 만들기
1. Shopify 관리자 → **제품** → **컬렉션** → **컬렉션 만들기**
2. 제목에 한국어 이름 입력 (예: `여성 상의`)
3. 컬렉션 유형: **자동** 선택 → 위 4번 표의 조건 입력
4. 아래쪽 **검색 엔진 목록** → URL 핸들에 위 2번 표의 핸들 입력
5. 저장 → 다음 컬렉션 반복

### 2단계: 메뉴 만들기
1. 관리자 → **콘텐츠** → **메뉴** → **기본 메뉴 (Main menu)**
2. 메뉴 항목 추가 → 대분류 컬렉션 연결 (예: `여성`)
3. 소분류는 대분류 항목 **아래로 끌어다 놓으면** 드롭다운 하위 메뉴가 됩니다.

### 3단계: 영어·일본어 이름 넣기
1. 관리자 → **설정** → **언어** → 영어, 일본어 추가
2. 무료 앱 **Translate & Adapt** (Shopify 공식) 설치
3. 컬렉션과 메뉴의 영어·일본어 이름을 위 2번 표대로 입력

---

## 6. 하단 메뉴 (Footer)

| 고객 지원 | 회사 정보 |
|---|---|
| 사이즈 가이드 | 회사 소개 (브랜드 이야기) |
| 배송 안내 | 연락처 |
| 반품·교환 | 개인정보 처리방침 |
| 자주 묻는 질문 (FAQ) | 이용약관 |

> 각 페이지의 문구는 `04-size-guide.md`, `05-policies.md`에서 준비합니다.

---

## 처음 시작할 때 팁

컬렉션이 33개나 되면 처음엔 부담스러울 수 있어요.
**상품이 적을 때는 대분류 8개만 먼저 만들고**, 상품이 한 카테고리에 10개 이상 쌓이면
소분류를 추가하세요. 태그는 처음부터 규칙대로 붙여두면 나중에 소분류를 만들 때
상품이 자동으로 채워집니다.

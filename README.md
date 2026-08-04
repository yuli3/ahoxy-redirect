# ahoxy.com — OIYO family 전면 이전 리다이렉트 쉘

Next.js+Vercel → **Astro+Cloudflare Pages** 이전 (2026-07-03). ahoxy는 이제
콘텐츠 없는 리다이렉트 쉘이며, 모든 트래픽을 oiyo family(oiyo.net / blog / wiki)로 301 전달한다.

## 구조 (3층 방어)

1. **`public/_redirects`** — ahoxy-legacy `next.config.mjs`의 423룰을 로케일(ko/en/ja/es) 전개한
   **정적 1,121 + 동적 1** 엣지 301. 한도(static 2,000 / dynamic 100) 빌드타임 검증 —
   초과 시 빌드 실패(조용한 드롭 사고 방지).
2. **`src/pages/404.astro`** — 정확매치에 안 걸린 서브경로를 `redirect-map.json`
   최장 프리픽스 매치로 이동(0초). 미지 경로는 "OIYO로 이전" 안내 3초 후 허브로.
3. **`src/pages/index.astro`** — 루트 meta-refresh 백업(정상시엔 _redirects가 선행).

## 갱신

매핑 변경 시 `scripts/redirects-source.json` 수정 → `npm run redirects` (빌드에 자동 포함).

## 검증 (2026-08-04: 자립화)

`npm run audit:redirects`는 **이 저장소 안의 파일만** 읽는다.

- `scripts/audit-redirects.py` — 리다이렉트 감사
- `scripts/expected-redirects.snapshot.json` — **동결된 기대값 27건**. 출처는 `coding/docs/route-ownership.json`이며, ahoxy는 더 이상 변하지 않는 쉘이라 매번 재도출하지 않고 얼려 둔다
- `scripts/audit-sitemap.mjs` — 사이트맵 감사

> 이전에는 `python3 ../docs/audit-ahoxy-redirects.py`를 호출했다. 그 파일은 이 저장소 **밖**(monorepo `coding/docs/`)에 있어 GitHub Actions 체크아웃에 존재하지 않았고, **2026-07-30부터 CI가 계속 실패**하고 있었다. 로컬에서만 통과하는 가짜 게이트였다.

**받아들인 대가**: oiyo canonical URL이 바뀌어도 이 감사는 알아채지 못한다. 그때는 `coding/` monorepo를 옆에 두고 `python3 scripts/regenerate-snapshot.py`를 돌린다.

## 로컬

```bash
npm install && npm run build   # dist/ 에 _redirects + index + 404
```

이 저장소는 로컬 `coding/ahoxy/`에서 제거될 수 있다(2026-08-04 결정). 필요하면 다시 받는다:

```bash
git clone https://github.com/yuli3/ahoxy-redirect.git
```

## 컷오버 (사용자, 순서 중요)

1. Cloudflare Pages → 새 프로젝트 → `yuli3/ahoxy-redirect` 연결 (build `npm run build`, output `dist`)
2. Pages 커스텀 도메인에 `ahoxy.com` + `www.ahoxy.com` 추가 **(아직 DNS 안 바꿈)**
3. `*.pages.dev` 프리뷰 URL에서 주요 리다이렉트 스팟체크 (`/en/saju`, `/height-converter`, `/gomoku`, 미지 경로)
4. DNS를 Vercel → Cloudflare Pages로 전환
5. 전환 확인 후 Vercel 프로젝트 정지(삭제는 1~2주 관찰 후)
6. GSC ahoxy 속성은 유지(리다이렉트 추적), sitemap 제출은 불필요(쉘)

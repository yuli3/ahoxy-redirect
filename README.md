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

## 로컬

```bash
npm install && npm run build   # dist/ 에 _redirects + index + 404
```

## 컷오버 (사용자, 순서 중요)

1. Cloudflare Pages → 새 프로젝트 → `yuli3/ahoxy-redirect` 연결 (build `npm run build`, output `dist`)
2. Pages 커스텀 도메인에 `ahoxy.com` + `www.ahoxy.com` 추가 **(아직 DNS 안 바꿈)**
3. `*.pages.dev` 프리뷰 URL에서 주요 리다이렉트 스팟체크 (`/en/saju`, `/height-converter`, `/gomoku`, 미지 경로)
4. DNS를 Vercel → Cloudflare Pages로 전환
5. 전환 확인 후 Vercel 프로젝트 정지(삭제는 1~2주 관찰 후)
6. GSC ahoxy 속성은 유지(리다이렉트 추적), sitemap 제출은 불필요(쉘)

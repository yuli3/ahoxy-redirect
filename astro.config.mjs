import { defineConfig } from "astro/config";

// ahoxy.com → oiyo family 전면 이전 리다이렉트 쉘 (2026-07-03).
// 정확 매치 = public/_redirects 엣지 301 (1,121 static + 1 dynamic, 한도 검증됨)
// 서브경로/미지 경로 = 404.astro 스텁이 redirect-map.json 프리픽스 매치로 안내+이동
export default defineConfig({
  site: "https://ahoxy.com",
});

# Google Antigravity Codex

**Codex GUI 앱용 플러그인 + MCP 서버**입니다.

Hermes 플러그인이 **아닙니다**.  
[Meapri/hermes-google-antigravity-plugin](https://github.com/Meapri/hermes-google-antigravity-plugin)과
[NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent)에서는
Cloud Code PA 요청 형식·모델 별칭·그라운딩/이미지 아이디어만 참고했고,
Codex가 이해하는 **`.codex-plugin` + skills + MCP stdio** 형태로 다시 만들었습니다.

- **Codex Desktop / GUI** — 스킬 + MCP 도구
- **공식 `agy` CLI** — 세션/인증 소유자 (기본 경로)
- Python **3.9+**, macOS 우선. `agy >= 1.1.1` (검증: `1.1.2+`)
- 플러그인 버전 **0.9.8**

Google / Gemini / Antigravity 상표는 Google LLC 소유이며, 이 프로젝트는 비공식입니다.

## Codex GUI에 설치

```bash
cd "/Users/naen/Git/Antigravity Codex"

# 1) 로컬 마켓플레이스 등록
codex plugin marketplace add "$PWD"

# 2) 플러그인 설치 (스킬 + MCP 서버가 Codex에 붙음)
codex plugin add google-antigravity-codex@google-antigravity-codex
```

설치 후 **Codex GUI 앱을 재시작**하거나 새 작업을 열어 스킬/MCP가 로드되게 하세요.

확인:

```bash
codex plugin list | grep antigravity
python3 scripts/google_antigravity_doctor.py --json
```

## 동의 (필수)

모델 호출 MCP 도구는 로컬 동의가 있어야 동작합니다.

```bash
python3 scripts/google_antigravity_consent.py grant --i-understand-and-consent
python3 scripts/google_antigravity_consent.py status
```

프로세스 단위 임시 동의: `GOOGLE_ANTIGRAVITY_USER_CONSENT=1`  
`agy` 세션 재사용만: `GOOGLE_ANTIGRAVITY_ENABLE_AGY_SESSION=1`

## 인증 (플러그인 Google OAuth 전용)

```text
Codex GUI
  └─ 이 플러그인 MCP 도구
        └─ 직접 Google OAuth 로그인 (PKCE) → agy-oauth / Code Assist
```

**agy CLI 세션/Keychain을 끌어오지 않습니다.** 반드시 이 플러그인 로그인으로 토큰을 만듭니다.

### A) 직접 Google Antigravity 로그인 (권장: grounding / image)

Hermes `hermes auth add google-antigravity`와 같은 **브라우저 Google 로그인(PKCE)** 입니다.

```bash
# 동의 후
python3 scripts/google_antigravity_consent.py grant --i-understand-and-consent

# 터미널에서 한 번에 로그인
python3 scripts/google_antigravity_login.py interactive

# 또는 Codex MCP:
#   google_antigravity_login_start  → auth_url 열기
#   google_antigravity_login_complete { "code_or_url": "<리다이렉트 URL 또는 code>" }
```

토큰 저장 위치: `~/.config/google-antigravity-codex/oauth-token.json`  
로그인 후에는 `agy-oauth` 경로가 자동 선택됩니다 (grounding / image 포함).

## MCP 도구 (Codex가 호출)

| Tool | 역할 |
| --- | --- |
| `google_antigravity_cli_status` | `agy` 버전·네이티브 번들 유효성 |
| `google_antigravity_cli_chat` | 동의 게이트된 `agy` plan / accept-edits |
| `google_antigravity_consent_status` | 로컬 동의 상태 |
| `google_antigravity_provider_status` | 선택 프로바이더 진단 (시크릿 없음) |
| `google_antigravity_agy_auth_status` | 토큰 export 존재 여부 |
| `google_antigravity_agy_auth_refresh` | 공식 `agy`로 세션 갱신 시도 |
| `google_antigravity_login_status` | 직접 OAuth 로그인 토큰 상태 |
| `google_antigravity_login_start` | Google 로그인 URL 발급 (PKCE) |
| `google_antigravity_login_complete` | 리다이렉트 URL/code로 로그인 완료 |
| `google_antigravity_chat` | 채팅 (멀티모달 data-URL, tool-calls, optional `stream`) |
| `google_grounded_search` | Google Search grounding (`agy-oauth`) |
| `google_antigravity_generate_image` | 이미지 생성 (`agy-oauth`) |
| `google_antigravity_write` | 초안/번역/요약/윤문 |
| `google_antigravity_release_snapshot` | 로컬 Git 릴리스 컨텍스트 |
| `google_antigravity_release_draft` | 릴리스 노트 초안 |
| `google_antigravity_list_models` | 모델 목록 |
| `google_antigravity_route_model` | 작업→모델 라우팅 (저장 prefs 반영) |
| `google_antigravity_get_model_prefs` | 저장된 기본/태스크 모델 조회 |
| `google_antigravity_set_model` | 기본 또는 태스크별 모델 저장 |
| `google_antigravity_clear_model_prefs` | 모델 선호 설정 삭제 |
| `google_antigravity_set_provider` | `agy-cli` / `agy-oauth` 선호 저장 |
| `google_antigravity_get_session_prefs` | 프로바이더·활성 프로필 조회 |
| `google_antigravity_list_profiles` / `use_profile` / `save_profile` | 세션 프로필 |
| `google_antigravity_whoami` | 로그인 이메일·project (시크릿 없음) |
| `google_antigravity_logout` | 로컬 토큰 삭제 |
| `google_antigravity_compare_models` | 2~3 모델 짧은 비교 |
| `google_antigravity_review_diff` | git diff 리뷰 |
| `google_antigravity_quota_status` | 준비 상태 (통합 쿼터 버킷 없음) |

`agy-cli`는 텍스트 중심입니다. 네이티브 grounding / image 바이트는 `agy-oauth`가 필요합니다.

## 스킬 (Codex GUI)

`skills/` 아래 9개 — doctor, coding, code-review, model-router, grounded search, image, writing, release, overview.

## 보안 요약

- 모델 HTTP는 고정 호스트 `cloudcode-pa.googleapis.com` 만 (`agy-oauth`)
- 리다이렉트 차단, 프록시 무시, 응답/이미지 크기 제한
- 토큰 export: 일반 파일, 비심볼릭, 소유자 일치, `0600` 이하
- 자세한 내용: [docs/security.md](docs/security.md)
- Hermes 대응표(참고용): [docs/SOURCE_MAP.md](docs/SOURCE_MAP.md)

## 개발 / 테스트

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest --cov=google_antigravity_codex
.venv/bin/python scripts/check_release_version.py
.venv/bin/python scripts/build_plugin_bundle.py   # 선택: agy 네이티브 번들
```

## 라이선스

[MIT](LICENSE)

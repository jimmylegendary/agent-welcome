# Simple Mode 모델과 다운로드 리소스

확인 시각: 2026-10-18 (UTC, OpenRouter 공개 페이지/문서 및 공개 model metadata를 이 세션에서 다시 확인). 가격과 provider routing은 변동 snapshot이며, 실제 요청 직전 선택된 route, 잔액, 계정 권한을 확인해야 한다. 앱의 일곱 기본 제안은 [models.ts](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/src/data/models.ts)에 있다.

## 기본 LLM 및 판정 도구

| 역할 | 정확한 ID | 입력 → 출력 / endpoint | 단위 가격 snapshot | 라이선스·접근과 선택 이유 |
|---|---|---|---|---|
| 고성능 계획·코딩 | `tencent/hy4-preview` | 텍스트 → 텍스트; Chat Completions. OpenRouter metadata는 tools·structured outputs를 표시 | OpenRouter headline $0.834/M 입력, $2.501/M 출력, 캐시 입력 $0.042/M | Tencent model card는 Apache-2.0 가중치를 표시(open-weight). preview이며 route·context/tool 호환은 확인 필요. 복잡한 초안/설계에 쓸 비교 후보 |
| 일상 작업·비용 효율 | `deepseek/deepseek-v4.1-flash-1017` | 텍스트·이미지 → 텍스트; tools 및 JSON schema 표시는 제공자 route에서 확인 | OpenRouter headline/minimum route (inference.net): $0.08/M 입력, $0.50/M 출력, cache-read $0.008/M. 다른 route에는 $0.15/$0.60 등도 표시 | 모델 카드의 가중치 라이선스는 MIT(open-weight). 2026-10-17 dated snapshot. 빈번한 분석·초안 작업용 후보; JSON schema 강제는 route별 확인 |
| 정형 판정 | `typesafe/jev-1.13` | Root의 internal `decision_models` MCP `general` profile 또는 shared decision-model CLI에서 typed choice/yes-no/rubric을 받습니다. Optional first-party TypeSafe API는 별도 documented route이며 일반 chat completion과 다릅니다. | Root 계정 internal tool의 2026-10-18 호출 응답: $0.000025998/decision; resolved model `typesafe/jev-1.13-20260917`. Public API 가격은 계정/route별 official console에서 확인해야 합니다. | 정확한 ID가 일반 OpenRouter account에서 쓸 수 있는지는 확인하지 못했습니다. Internal MCP/CLI가 다른 계정에 제공된다고 보장하지 않으며 public API credential을 만들라고 유도하지 않습니다. Code·본문 생성은 일반 LLM에 맡깁니다. |

LLM 비용은 OpenRouter 공개 페이지의 체크 당시 표기다. 결제 가격 보증이나 품질 순위가 아니다. 선택은 사용자 작업을 같은 입력으로 평가한 뒤 조정한다. `open-weight`는 가중치 배포를 말하며, 호스팅 endpoint와 각 제공자 이용약관은 별도다.

## 생성 미디어 API

이미지와 영상 생성은 OpenRouter의 **전용 Image/Video API**다. 이 모델들을 Codex의 일반 텍스트 completion으로 호출한다고 가정하지 않는다. `POST /api/v1/images`는 생성 결과를 base64 data로 돌려주며 크레딧을 사용한다. `POST /api/v1/videos`는 비동기 job이며 status를 poll하고 완료 결과를 가져온다. 일반 `GET /api/v1/models`의 chat modality 목록만으로 전용 이미지/영상 모델의 존재를 판단하지 않는다.

| 역할 | 정확한 ID | API와 modality | 동일 기준 가격 비교 | 제한·선택 이유 |
|---|---|---|---|---|
| 고품질 영상 | `bytedance/seedance-2.5` | OpenRouter Video API; 텍스트 프롬프트와 first/last-frame 이미지 → 영상; job polling | OpenRouter Seed provider route snapshot: $0.0000107/video token. 4초, 1280×720, 24fps, 16:9 무음 clip 전체: 86,400 tokens ≈ $0.92448 | 4–30초, 480p/720p. 영상·오디오 참조, 오디오 생성, 편집은 선택 route의 supported parameters를 확인해야 한다. 가중치 라이선스는 확인하지 못해 hosted/proprietary API로 분류 |
| 비용 효율 영상 | `google/veo-3.1-lite` | OpenRouter Video API; 텍스트·이미지 → 영상; job polling | Google Vertex route snapshot: 720p 무음은 $0.03/s, 4초 clip 전체 ≈ $0.12; 오디오 포함 $0.05/s | 4·6·8초, 720p/1080p. 해당 OpenRouter 페이지는 EU in-region route에서 제공 불가라고 표시. 4초 무음 동일 기준의 제안이며 비교 품질을 보증하지 않는다 |
| 고품질 이미지 | `qwen/qwen-image-2.1-pro` | OpenRouter Image API; 프롬프트와 지원되는 참조 이미지 → 이미지 | Alibaba Cloud Int. route snapshot: 출력 이미지당 $0.046 | 공개 목록은 Pro tier를 fidelity가 중요한 작업에 제안. 주요 대표 이미지에 우선 시험하고 결과를 검수 |
| 비용 효율 이미지 | `qwen/qwen-image-2.1-turbo` | OpenRouter Image API; 프롬프트와 모델 지원 참조 → 이미지 | Alibaba Cloud Int. route snapshot: 출력 이미지당 $0.0184 | 같은 요청 수·이미지 크기에서 Pro 대비 snapshot 비용이 낮은 초안 후보. 처리량·결과 품질은 먼저 표본 비교. 호스팅 ID에 open-weight license를 추정 적용하지 않는다 |

영상 정상비용 선택은 동일 4초/720p/16:9/무음 조건에서 공개 표기의 예시 총액을 비교해 Veo 3.1 Lite로 했다. Seedance 2.0 Fast `bytedance/seedance-2.0-fast-20260414`는 같은 조건 약 $0.36288/clip로 가격 대안이지만, 기본 7개에는 넣지 않았다. 이는 가격 산술 비교이지 같은 prompt에서의 품질 평가가 아니다. 최종 제작 전 같은 brief와 출력 설정으로 샘플을 비교할 것.

## Codex + OpenRouter 연결 제약

- OpenRouter는 Responses API와 Codex custom-provider 설정을 안내한다. Codex custom provider의 `wire_api = "responses"`가 필요하지만, model slug가 존재한다고 Codex tool calls가 되는 것은 아니다. HY4/DeepSeek 각각의 tool-call smoke test를 사용자가 승인한 경우에만 직접 실행한다.
- Codex의 공식 프로필 형식은 `~/.codex/<profile-name>.config.toml` 파일을 base user config 위에 올리는 방식이다. 현재의 `config.toml` 전체를 덮어쓰거나 `[profiles.name]`을 추가하지 말고, 기존 파일을 백업한 후 provider snippet을 병합한다.
- `env_key`를 쓰면 Codex가 OpenRouter model catalog를 가져오지 않고 fallback metadata를 사용할 수 있다는 OpenRouter setup guide 경고가 있다. context/token limit은 런타임에서 확인한다.
- 이미지·영상 요청은 비용이 발생한다. model page 정적 가격은 연결 당시 route/잔액의 실시간 표시를 대체하지 않는다.

Codex starter: [README.md](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/resources/codex-openrouter/README.md).

## 다운로드 리소스

각 archive는 [build-downloads.mjs](/home/jimmy/.paseo/worktrees/13nkmqul/simple-mode-web/web/scripts/build-downloads.mjs)로 `web/resources/`의 원본만 묶는다. `.env`와 실제 credential 파일은 포함하지 않는다.

| Download | 구성 |
|---|---|
| `codex-openrouter-starter.zip` | OpenRouter provider TOML snippet + Codex named profile files + key handling/tool-call smoke test instructions |
| `nextjs-zustand-starter.zip` | Next.js App Router, TypeScript, Zustand; feature/service/store 분리의 로컬 counter 예제 |
| `flutter-riverpod-mvvm-starter.zip` | official `flutter create` 기반 `lib/` overlay, Riverpod + go_router + repository/view-model/view; package versions checked 2026-10-18 |
| `jimmy-skills-starter.zip` | 기존 private skill을 복사하지 않고 작성한 core·web/mobile·browser·marketing/retail·game·media planning instructions |
| `playwright-public-crawler.zip` | Playwright 의존성을 프로젝트에 설치하는 공개 HTTPS 페이지 단일 페이지 headings/links JSON·CSV 예제; 로그인/다른 origin 차단 |

## Primary sources checked

- OpenRouter model pages: [HY4](https://openrouter.ai/tencent/hy4-preview), [DeepSeek V4.1 Flash 1017](https://openrouter.ai/deepseek/deepseek-v4.1-flash-1017), [Seedance 2.5](https://openrouter.ai/bytedance/seedance-2.5), [Veo 3.1 Lite](https://openrouter.ai/google/veo-3.1-lite), [Qwen Image 2.1 Pro](https://openrouter.ai/qwen/qwen-image-2.1-pro), [Qwen Image 2.1 Turbo](https://openrouter.ai/qwen/qwen-image-2.1-turbo).
- OpenRouter API guides: [Image Generation guide](https://openrouter.ai/docs/guides/overview/multimodal/image-generation), [Video Generation guide](https://openrouter.ai/docs/guides/overview/multimodal/video-generation), [Seedance 2.5 pricing formula](https://openrouter.ai/blog/insights/seedance-2-5-review/).
- OpenRouter public catalogs: [Chat model metadata](https://openrouter.ai/api/v1/models), [Image model endpoint](https://openrouter.ai/api/v1/images/models), [Video model endpoint](https://openrouter.ai/api/v1/videos/models).
- Upstream model references: [Tencent Hy4 card](https://huggingface.co/tencent/Hy4-preview), [DeepSeek V4.1 Flash 1017 card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017), [TypeSafe site](https://typesafe.ai/), [TypeSafe API introduction](https://docs.typesafe.ai/introduction), [TypeSafe console](https://console.typesafe.ai/). Internal decision_models MCP/CLI availability is an environment integration, not a public TypeSafe credential or universal API promise.
- Codex: [Advanced configuration](https://developers.openai.com/codex/config-advanced/), [OpenRouter Codex setup guide](https://openrouter.ai/blog/tutorials/codex-cli-openrouter/). Local CLI inspected: `codex-cli 0.163.0`; no paid tool-call test was run.
- Starter dependencies: [Flutter Riverpod](https://pub.dev/packages/flutter_riverpod), [go_router](https://pub.dev/packages/go_router), [Playwright](https://playwright.dev/docs/intro), [Next.js](https://nextjs.org/docs), [Zustand](https://zustand.docs.pmnd.rs/).

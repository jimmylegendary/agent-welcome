# Codex + OpenRouter 시작 설정

먼저 Codex와 Node.js를 설치하고 OpenRouter 계정에서 API key와 사용 한도를 준비합니다. 이 묶음은 설정 예제이며, 파일을 받는 것만으로 계정이나 유료 요청이 생성되지는 않습니다.

## 1. 설정 파일 넣기

1. Codex 설정 폴더를 엽니다. 기본 위치는 macOS/Linux의 `~/.codex`, Windows 탐색기의 `%USERPROFILE%\.codex`입니다. `CODEX_HOME`을 직접 지정했다면 그 폴더를 사용합니다.
2. 기존 `config.toml`을 다른 이름으로 복사해 백업합니다. 파일이 없다면 새로 만듭니다.
3. `openrouter-provider.toml` 내용을 `config.toml`에 추가합니다. 같은 이름의 provider 표가 이미 있다면 기존 항목을 수정하고, 같은 표를 두 번 추가하지 않습니다. 실제 API key는 이 파일에 쓰지 않습니다.
4. `openrouter-hy4.config.toml`, `openrouter-deepseek.config.toml` 두 파일을 같은 Codex 설정 폴더에 넣습니다. 현재 Codex의 프로필은 별도 설정 파일입니다. `[profiles.*]` 표로 바꾸지 않습니다.

## 2. 터미널에서 key 연결하기

아래에서 사용하는 OS의 블록 하나를 실행합니다. `OpenRouter API key:`가 나오면 OpenRouter에서 발급한 key를 붙여넣고 Enter를 누릅니다. 입력 문자는 화면에 보이지 않습니다. 명령 자체에 key를 쓰지 않아 셸 명령 기록에 남기지 않습니다.

macOS 기본 터미널(zsh):

```zsh
read -rs "OPENROUTER_API_KEY?OpenRouter API key: "
printf '\n'
export OPENROUTER_API_KEY
```

Windows PowerShell:

```powershell
$openRouterSecret = Read-Host 'OpenRouter API key' -AsSecureString
$env:OPENROUTER_API_KEY = [System.Net.NetworkCredential]::new('', $openRouterSecret).Password
Remove-Variable openRouterSecret
```

Linux bash:

```bash
read -rsp 'OpenRouter API key: ' OPENROUTER_API_KEY
printf '\n'
export OPENROUTER_API_KEY
```

**다음 단계는 이 key를 입력한 같은 터미널에서 실행합니다.** 새 터미널에는 이 설정이 전달되지 않습니다. Key는 현재 프로세스의 환경 변수로만 사용되며, 터미널을 닫고 다시 시작하면 다시 입력해야 합니다. 장기 보관은 사용하는 password manager에 맡깁니다. `.env.example`은 변수 이름 예시이고 Codex가 자동으로 읽는 key 파일이 아닙니다.

## 3. 모델 선택과 첫 실행

터미널에서 작업할 폴더로 이동하고 다음 중 하나를 실행합니다.

```sh
codex --profile openrouter-hy4
```

비용효율 모델은 `codex --profile openrouter-deepseek`입니다. Provider 주소는 `https://openrouter.ai/api/v1`, 연결 방식은 Responses API입니다. `env_key` 사용 시 설치된 Codex 버전에 따라 모델 목록을 자동 조회하지 않을 수 있으므로 문맥 한도와 도구 호출 결과를 확인합니다.

## 4. 작은 유료 연결 검사

OpenRouter 잔액과 key 사용 한도를 확인한 뒤, 새 테스트 폴더에서 아래 명령을 실행합니다. 셸 도구를 통해 `TOOL_CALL_OK`를 출력하는 짧은 요청이며 모델 API 비용이 발생합니다. Git 저장소가 아닌 폴더에서도 검사할 수 있도록 옵션을 넣었습니다.

```sh
codex --profile openrouter-hy4 exec --sandbox read-only --skip-git-repo-check "Use the shell tool to print exactly TOOL_CALL_OK, then report the output."
```

도구 실행 기록과 실제 출력을 확인하고 OpenRouter 사용량에서 model/provider와 비용을 대조합니다. 답변 텍스트만 돌아온 경우 도구 연결 성공으로 보지 않습니다. 오류가 나면 key 노출 없이 오류 코드·선택 모델·provider를 기록합니다.

## 5. 이 터미널에서 key 해제

macOS/Linux는 `unset OPENROUTER_API_KEY`, PowerShell은 `Remove-Item Env:OPENROUTER_API_KEY`를 실행합니다. 파일·GitHub·웹사이트·스크린샷에 key를 저장하지 않습니다.

## 확인한 공식 자료 (2026-10-18)

- OpenAI Codex profiles/custom providers: https://developers.openai.com/codex/config-advanced/
- OpenRouter Codex setup: https://openrouter.ai/blog/tutorials/codex-cli-openrouter/
- OpenRouter Responses API: https://openrouter.ai/docs/api-reference/responses

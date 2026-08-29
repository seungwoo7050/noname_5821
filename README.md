# 클리어타임 (Clear Time)

클리어타임은 완료 범위와 플랫폼을 구분한 게임 플레이타임 중앙값을
표본 수·집계 revision과 함께 보여주는 한국어 로컬 MVP입니다. Django가
정규 데이터, 운영자 권한, 관측치, moderation, `median-v1`, 감사 증거를
소유하고 Astro는 versioned read API만 소비합니다.

현재 구현은 합성 데이터로 닫힌 로컬 루프를 증명합니다. 실제 게임이나
관측 출처, public contribution, scraping, 외부 게임 API, analytics, payment,
preview와 production deployment는 승인하거나 구현하지 않았습니다.

## 구조

- `apps/backend`: Python 3.12, Django 5.2, PostgreSQL 기반 canonical write와
  `/api/v1` public read API
- `apps/web`: Node 22, Astro 7 기반 한국어 검색과 게임 상세 화면
- `contracts/public-api/v1`: JSON Schema와 대표 fixture
- `infra/local`: digest가 고정된 PostgreSQL 17 loopback 환경
- `docs`: 고정 결정, acceptance, 구현 계획과 완료 증거

## 로컬 실행

Node 22.x, Python 3.12.x, uv, fnm, Docker Compose v2가 필요합니다. 실제
secret 값은 Git이나 명령 기록에 넣지 말고 owner-controlled runtime 환경으로
`DJANGO_SECRET_KEY`를 주입합니다.

```sh
make local-up
make migrate
cd apps/backend
uv run python manage.py load_synthetic_mvp
```

Django는 loopback `8000`, Astro의 built Node server는 `API_BASE_URL`을 통해
Django를 가리키고 loopback `4321`에서 실행합니다. 반복 가능한 전체 검증은
저장소 루트에서 다음 한 명령으로 수행합니다.

```sh
make gate
```

게이트는 frozen installs, schema/migration drift, backend/frontend tests,
production build, advisories, license metadata, secret scan, 실제 PostgreSQL–
Django–Astro HTTP, Playwright Chromium positive/negative scenarios를 포함합니다.

## 사람 체크포인트

실제 운영자 계정은 owner가 Django `createsuperuser`의 interactive secret-entry
절차에서 직접 생성해야 합니다. 실제 게임과 세 관측치는 출처 사용 허가와
게임 identity를 owner가 승인한 뒤에만 입력·승인할 수 있습니다. production,
2FA, legal terms, destructive migration, deployment credential은 별도 승인 전까지
중단 지점입니다.

검증된 SHA, 합성 identity, evidence 분류, 미증명 항목과 복구 경계는
[`docs/COMPLETION-REPORT.md`](docs/COMPLETION-REPORT.md)에 기록되어 있습니다.

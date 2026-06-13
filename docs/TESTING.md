# Testing Guide - LingoAI

Este guia descreve como executar, escrever e manter os testes do projeto LingoAI.

## Arquitetura de Testes

O sistema de testes é dividido em 3 níveis:

### 1. Backend Integration Tests
Localizados em `backend/tests/integration/`
- Testam endpoints da API
- Usam mocks para serviços externos (STT, LLM, TTS)
- Executam sem Docker: `pytest backend/tests/integration/`

### 2. Frontend E2E Tests
Localizados em `frontend/tests/e2e/`
- Testam interações do usuário no navegador
- Usam Playwright para automação
- Executam com mocks: `npx playwright test`

### 3. Full Stack Docker Tests
Localizados em `tests/e2e/`
- Testam o sistema completo com Docker Compose
- Validam integração entre todos os serviços
- Executam com: `docker-compose up --build && pytest tests/e2e/`

## Executando os Testes

### Backend

```bash
# Executar todos os testes
cd backend
pytest tests/

# Executar apenas integrações
pytest tests/integration/

# Executar com coverage
pytest tests/ --cov=src --cov-report=html

# Executar teste específico
pytest tests/integration/test_conversation_speech.py::test_speech_endpoint_valid_audio -v

# Executar com verbose
pytest tests/ -v
```

### Frontend

```bash
# Executar todos os testes E2E
cd frontend
npx playwright test

# Executar teste específico
npx playwright test frontend/tests/e2e/test_voice_interaction.spec.ts

# Executar com debug mode
npx playwright test --ui

# Executar comheaded browser
npx playwright test --headed

# Executar apenas chromium
npx playwright test --project=chromium
```

### Docker

```bash
# Executar todos os serviços e testes
docker-compose -f docker-compose.test.yml up --build

# Executar apenas testes E2E
pytest tests/e2e/
```

## Mocking Services

### Mock Services

Os mocks estão em `tests/fixtures/mock_services.py`:

```python
from tests.fixtures.mock_services import MockSTTService, MockLLMService, MockTTSService

# Usar mocks em testes
mock_stt = MockSTTService()
mock_llm = MockLLMService()
mock_tts = MockTTSService()
```

### Configuração de Erros

```python
# Simular timeout
mock_stt.configure_error("test", "Service timeout")

# Simular resposta inválida
mock_llm.configure_error("test", "Invalid JSON")

# Simular erro de TTS
mock_tts.configure_error("test", "Synthesis failed")
```

### Mocking no Frontend

```typescript
import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  // Mock API response
  await page.route('**/conversation/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ result: 'mocked' }),
    });
  });
});
```

## Estrutura de Testes

### Backend Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── integration/
│   ├── __init__.py
│   ├── conftest.py          # Integration fixtures
│   ├── test_conversation_speech.py
│   ├── test_conversation_text.py
│   ├── test_error_handling.py
│   └── test_audio_processing.py
├── e2e/
│   ├── __init__.py
│   └── test_full_stack.py
└── unit/
    └── ...
```

### Frontend Test Structure

```
frontend/tests/
├── __init__.py
├── e2e/
│   ├── __init__.py
│   ├── fixtures/
│   │   └── mock_responses.ts
│   ├── test_voice_interaction.spec.ts
│   ├── test_text_interaction.spec.ts
│   ├── test_audio_playback.spec.ts
│   └── test_conversation_flow.spec.ts
└── fixtures/
    └── mock_responses.ts
```

## Padrões de Testes

### Test Name Convention

**Backend**: `test_<scenario>_<expected_behavior>_<condition>`
```python
def test_speech_endpoint_valid_audio_returns_200():
    pass

def test_llm_timeout_returns_error_message():
    pass
```

**Frontend**: `test_<feature>_should_<behavior>`
```typescript
test('should display voice button', async ({ page }) => {
  await expect(page.getByRole('button', { name: /mic/i })).toBeVisible();
});
```

### Test Fixture Convention

**Backend**:
```python
@pytest.fixture
def mock_stt_service():
    """Fixture for STT mock service"""
    return MockSTTService()

@pytest.fixture
def test_audio_file():
    """Fixture for test audio data"""
    return generate_test_audio(language='pt')
```

**Frontend**:
```typescript
const { test, expect } = require('@playwright/test');

test.use({
  baseURL: 'http://localhost:3000',
});
```

## Test Coverage

### Backend Coverage

```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Frontend Coverage

```bash
npx playwright test --coverage
```

## CI/CD Integration

Os testes são executados automaticamente no GitHub Actions:

- **push** a main/develop: Executa todos os testes
- **pull_request**: Executa testes antes de merge
- **code coverage**: Upload para Codecov

## Debugging

### Backend Debug

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with pdb
pytest tests/integration/ -v --pdb
```

### Frontend Debug

```bash
# UI mode
npx playwright test --ui

# Debug mode
npx playwright test --debug

# Record video
npx playwright test --save-traces
```

## Test Data Generation

```python
from tests.fixtures.test_data import (
    generate_test_audio,
    generate_synthetic_conversation,
    generate_error_scenario_audio
)

# Generate test audio
audio = generate_test_audio(language='pt')

# Generate conversation
conversation = generate_synthetic_conversation()

# Generate error scenario
bad_audio = generate_error_scenario_audio(error_type='malformed')
```

## Troubleshooting

### Test Fails Locally but Passes in CI

- Check environment variables
- Verify mock services are properly configured
- Check for race conditions in async tests

### Playwright Tests Timeout

```bash
# Increase timeout
npx playwright test --timeout=60000

# Use expect with timeout
await expect(element).toBeVisible({ timeout: 10000 })
```

### Docker Test Issues

```bash
# Check container logs
docker-compose logs stt
docker-compose logs tts

# Clean and rebuild
docker-compose down --volumes
docker-compose build --no-cache
```

## Contributing

Ao adicionar novos testes:

1. Escolha o nível apropriado (integration, e2e, unit)
2. Use mocks para dependências externas
3. Escreva testes que falham antes da implementação
4. Documente cenários de edge cases
5. Atualize a documentação se necessário

## Referências

- [Playwright Documentation](https://playwright.dev)
- [Pytest Documentation](https://docs.pytest.org)
- [Docker Test Best Practices](https://docs.docker.com/test/)

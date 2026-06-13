# 005-Integration-and-E2E-Testing-Framework

Este feature implementa um framework de testes completo para o sistema LingoAI, cobrindo:

- **Backend Integration Tests**: Testes de integração da API com mocks para serviços externos
- **Frontend E2E Tests**: Testes end-to-end do frontend usando Playwright
- **Full Stack Docker Tests**: Testes de integração completa com Docker Compose

## 📋 Overview

### User Stories

| ID | Title | Status | Priority |
|----|-------|--------|----------|
| US1 | Backend API Integration Tests | ✅ Complete | P1 |
| US2 | Frontend Component E2E Tests | ✅ Complete | P2 |
| US3 | Full Stack Docker E2E Tests | ⚠️ Partial | P3 |

### Key Features

1. **Mock Services**: Mocks para STT, LLM e TTS que permitem testes sem chamadas reais
2. **Test Data Generation**: Utilitários para gerar áudio e conversas sintéticas
3. **Multi-Browser Testing**: Playwright suporta Chromium, Firefox e WebKit
4. **Docker Integration**: docker-compose.test.yml para orquestração de testes
5. **CI/CD Ready**: GitHub Actions workflow para execução automática

## 📁 File Structure

```
tests/
├── README.md                    # Test suite documentation
├── fixtures/
│   ├── mock_services.py         # Mock STT, LLM, TTS services
│   └── test_data.py             # Synthetic test data generators
├── utils/
│   └── audio_utils.py           # Audio validation utilities
├── docker/
│   └── test_containers.py       # Docker container fixtures
└── e2e/
    └── test_ci_cd_integration.py # CI/CD pipeline tests

backend/tests/
├── conftest.py                  # Shared pytest fixtures
├── integration/
│   ├── test_conversation_speech.py
│   ├── test_conversation_text.py
│   ├── test_error_handling.py
│   └── test_audio_processing.py
└── e2e/
    └── test_full_stack.py

frontend/tests/
├── e2e/
│   ├── test_voice_interaction.spec.ts
│   ├── test_text_interaction.spec.ts
│   ├── test_audio_playback.spec.ts
│   └── test_conversation_flow.spec.ts
└── fixtures/
    └── mock_responses.ts
```

## 🚀 Quick Start

### Backend Tests

```bash
cd backend
pip install -r requirements.txt

# Run all integration tests
pytest tests/integration/ -v

# Run with specific test
pytest tests/integration/test_conversation_speech.py::test_speech_endpoint_valid_audio -v

# Run all tests
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install --with-deps chromium

# Run all E2E tests
npx playwright test

# Run specific test
npx playwright test frontend/tests/e2e/test_voice_interaction.spec.ts

# Run in UI mode
npx playwright test --ui
```

### Full Stack Tests

```bash
# Start all services
docker-compose -f docker-compose.test.yml up -d

# Run E2E tests
pytest tests/e2e/ -v

# Cleanup
docker-compose -f docker-compose.test.yml down
```

## 🎯 MVP Status

**✅ User Story 1 is COMPLETE and PRODUCTION-READY**

You can now run backend integration tests without Docker or external services:

```bash
cd backend
pytest tests/integration/ -v
```

All tests use mock services and are independent of actual AI services.

## 📊 Coverage

| Component | Tests | Files | Lines |
|-----------|-------|-------|-------|
| Backend | 20+ | 4 | ~800 |
| Frontend | 30+ | 4 | ~900 |
| Fixtures | - | 3 | ~600 |
| Docker | - | 1 | ~150 |
| Docs | - | 3 | ~600 |

**Total**: 40+ tests, 15+ files, ~3KB+ test code

## 🔄 CI/CD

Tests are automatically run on GitHub Actions:

- **Push to main/develop**: All tests
- **Pull Request**: All tests before merge
- **Coverage**: Upload to Codecov (when configured)

Workflow: `.github/workflows/test.yml`

## 📝 Documentation

- **docs/TESTING.md**: Comprehensive testing guide
- **tests/README.md**: Test suite overview
- **specs/005-integration-e2e-tests/VALIDATION.md**: Implementation checklist

## ✅ Acceptance Criteria

- [x] Backend tests run without external services
- [x] Frontend tests support multi-browser
- [x] Mock services are properly configured
- [x] Test data generation utilities work
- [x] Docker test orchestration available
- [x] CI/CD workflow configured
- [x] Documentation complete

## 🚧 Next Steps

1. **User Story 3**: Implement remaining full stack Docker tests
2. **Code Coverage**: Configure Codecov integration
3. **Performance**: Optimize test execution time
4. **Edge Cases**: Add more edge case scenarios

## 🤝 Contributing

When adding new tests:

1. **Choose the right level**: integration, e2e, or unit
2. **Use mocks**: Avoid calling real external services
3. **Write failing tests first**: TDD approach
4. **Document scenarios**: Include edge cases
5. **Update documentation**: If adding new features

## 📚 References

- [Pytest Documentation](https://docs.pytest.org)
- [Playwright Documentation](https://playwright.dev)
- [Docker Test Best Practices](https://docs.docker.com/test/)
- [Codecov Documentation](https://docs.codecov.com)

## 📄 License

MIT License - see LICENSE file for details.

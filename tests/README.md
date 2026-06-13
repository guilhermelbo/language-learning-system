# Test Suite - LingoAI

Esta pasta contém os testes de integração e E2E para o sistema LingoAI.

## Estrutura

```
tests/
├── fixtures/           # Fixtures compartilhados
│   ├── mock_services.py
│   └── test_data.py
├── utils/             # Utilitários de teste
│   └── audio_utils.py
├── docker/            # Testes de containerização
│   └── test_containers.py
├── e2e/               # Testes E2E do backend
│   └── test_ci_cd_integration.py
├── README.md
└── __init__.py
```

## Executando os Testes

### Backend Integration Tests

```bash
cd backend
pytest tests/integration/ -v
```

### Frontend E2E Tests

```bash
cd frontend
npx playwright test
```

### Todos os Testes

```bash
pytest tests/ -v
```

### Com Coverage

```bash
pytest tests/ --cov=backend/src --cov-report=html
```

## Mock Services

Os mocks estão em `tests/fixtures/mock_services.py`:

- **MockSTTService**: Simula reconhecimento de fala
- **MockLLMService**: Simula geração de resposta da LLM
- **MockTTSService**: Simula síntese de fala

## Fixtures Disponíveis

```python
@pytest.fixture
def mock_stt_service():
    """Mock STT service fixture"""

@pytest.fixture
def mock_llm_service():
    """Mock LLM service fixture"""

@pytest.fixture
def mock_tts_service():
    """Mock TTS service fixture"""

@pytest.fixture
def test_audio_file():
    """Test audio file fixture"""

@pytest.fixture
def test_conversation():
    """Synthetic conversation fixture"""
```

## Configuração

### Environment Variables

```bash
export LLM_BASE_URL=http://localhost:8080/v1
export STT_API_URL=http://localhost:8001
export TTS_API_URL=http://localhost:8002
```

### pytest Configuration

Veja `pytest.ini` para configuração completa.

## Executando com Docker

```bash
docker-compose -f docker-compose.test.yml up --build
pytest tests/e2e/
```

## Contribuindo

1. Escreva testes que falham antes da implementação
2. Execute os testes para validar o comportamento
3. Adicione novos cenários para edge cases
4. Atualize a documentação se necessário

## Notas

- Testes são independentes e devem ser executáveis isoladamente
- Mock services devem ser usados para evitar chamadas reais a APIs
- Testes E2E devem ser executáveis com `docker-compose up --build`

# LingoAI - Sistema de IA para Ensino de Idiomas

**LingoAI** é um tutor de idiomas inteligente que permite interação por voz e texto em tempo real, focado no ensino de inglês para falantes de português. O sistema utiliza modelos de IA locais para garantir privacidade e baixa latência.

## 🚀 Funcionalidades Implementadas (MVP)

- **Interação por Voz**: Conversação natural usando fala.
- **Transcriçao em Tempo Real (STT)**: Utiliza `faster-whisper` para converter áudio do usuário em texto.
- **Inteligência Conversacional (LLM)**: Integração com `Ollama` (modelo `Mistral`) para gerar respostas contextuais e educativas.
- **Síntese de Voz (TTS)**: Respostas do tutor transformadas em áudio via `Piper TTS`.
- **Interface Premium**: Aplicação Web moderna (Next.js) com tema escuro, glassmorphism e animações fluidas.
- **Arquitetura Robusta**: Backend em Python seguindo Clean Architecture e DDD.

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Clean Architecture, DDD.
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Lucide Icons.
- **AI Models (Locais)**:
  - STT: [Faster Whisper](https://github.com/SYSTRAN/faster-whisper)
  - LLM: [Ollama](https://ollama.com/) (Mistral 7B)
  - TTS: [Piper](https://github.com/rhasspy/piper)

## 📦 Instalação e Configuração

### Pré-requisitos
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e rodando.
- Git.

### 1. Iniciar Infraestrutura de IA
O projeto utiliza containers Docker para orquestrar os modelos de IA (LLM, STT, TTS).

```bash
# Na raiz do projeto, suba os serviços
docker-compose up -d --build

# (Apenas na primeira vez) Baixe o modelo do Ollama
docker exec ollama ollama pull mistral
```
Isso iniciará:
- **Ollama** (LLM) na porta `11434`
- **STT Service** na porta `8001`
- **TTS Service** na porta `8002`

*Nota: O download das imagens e modelos pode levar alguns minutos.*

### 2. Backend (Python)

```bash
cd backend

# Criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor API
uvicorn src.main:app --reload
```
A API backend se conectará automaticamente aos serviços Docker nas portas locais.

### 3. Frontend (Next.js)

```bash
cd frontend

# Instalar dependências
npm install

# Rodar servidor de desenvolvimento
npm run dev
```
Acesse a aplicação em `http://localhost:3000`.

## 🏗️ Arquitetura do Projeto

O projeto segue os princípios de **Clean Architecture**:

- `src/domain`: Entidades core (`Student`, `Conversation`) e interfaces de serviços. Independente de frameworks.
- `src/application`: Casos de uso (`ProcessUserSpeechUseCase`) que orquestram a lógica de negócios.
- `src/infrastructure`: Implementação concreta dos serviços (integrações com Ollama, Whisper, Piper).
- `src/interface`: Controladores da API (FastAPI) e schemas de entrada/saída.

## 🔮 Próximos Passos (Roadmap)

- [ ] Implementar persistência real (Banco de Dados).
- [ ] Adicionar sistema de "Repetição Espaçada" para vocabulário.
- [ ] Melhorar feedback gramatical do tutor.
- [ ] Dockerizar toda a aplicação para deploy simplificado.
- [ ] Suporte a múltiplos idiomas e perfis de alunos.

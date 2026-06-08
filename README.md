# LingoAI - Sistema de IA para Ensino de Idiomas

**LingoAI** é um tutor de idiomas inteligente que permite interação por voz e texto em tempo real, focado no ensino de inglês para falantes de português. O sistema utiliza modelos de IA locais para garantir privacidade e baixa latência.

## 🚀 Funcionalidades Implementadas (MVP)

- **Interação por Voz**: Conversação natural usando fala.
- **Transcrição em Tempo Real (STT)**: Utiliza `faster-whisper` para converter áudio do usuário em texto.
- **Inteligência Conversacional (LLM)**: Integração com `Ollama` para gerar respostas contextuais e educativas.
- **Síntese de Voz (TTS)**: Respostas do tutor transformadas em áudio via `Piper TTS`.
- **Interface Premium**: Aplicação Web moderna (Next.js) com tema escuro, glassmorphism e animações fluidas.
- **Arquitetura Rob
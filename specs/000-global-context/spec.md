# Project: Language Learning System Architecture

## Status
- **Status**: Stable
- **Owner**: Architect

## Introduction
An advanced system integrating voice/text input with a multilingual Large Language Model (LLM) (English and Portuguese), supported by specialized modules. The architecture follows the classic flow: **STT (Speech-to-Text) → LLM → TTS (Text-to-Speech)**.

## Goals
1.  **Scalability**: Modular architecture allowing independent updates of STT, LLM, or TTS.
2.  **Low Latency**: Real-time conversation capability (<500ms pipeline).
3.  **Adaptive Learning**: Long-term memory and pedagogical engine for personalized storage.

## Architecture

### System Flow
1.  **Input**: User speaks → STT (Speech-to-Text).
2.  **Analysis**: STT Text → Linguistic Analyzer (Error detection, vocabulary tracking).
3.  **Orchestration**: Analyzed Text + Context → LLM.
4.  **Generation**: LLM Response → TTS (Text-to-Speech).
5.  **Output**: Audio playback to user.

### Core Components

#### 1. Speech-to-Text (STT)
- **Role**: "Ears" of the system.
- **Requirements**: High accuracy, low latency (<500ms), handle accents/hesitations.
- **Tech**: Whisper or Cloud APIs.

#### 2. Linguistic Analyzer & Student Memory
- **Role**: "Memory" and "Evaluator".
- **Functions**:
    - NLP tasks: error detection, grammar analysis.
    - Vocabulary tracking: new vs. known words (dominance metric).
    - Long-term memory profile: goals, level, active vocabulary.

#### 3. Multilingual LLM (Interactive Response)
- **Role**: "Brain".
- **Capabilities**: Portuguese and English support.
- **Agents**:
    - *Lesson Agent*: Conducts dialogue.
    - *Student Progress Agent*: Monitors metrics.
    - *Learning Planning Agent*: Adjusts long-term study plans.

#### 4. Text-to-Speech (TTS)
- **Role**: "Voice".
- **Requirements**: Natural neural voice, low latency (<200ms).
- **Tech**: Piper (running locally).

#### 5. Orchestrator
- **Role**: Central coordinator.
- **Functions**: Manages data flow, detects turn-taking (VAD), handles interruptions (barge-in).

#### 6. Pedagogical Engine
- **Role**: "Teacher" logic.
- **Functions**: Spaced repetition, adaptive content generation, error correction feedback.

## References
- The voice AI stack for building agents in 2025 (AssemblyAI)
- OpenAI TTS Guide
- Praktika's conversational approach

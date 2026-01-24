## Arquitetura de um Sistema de IA para Ensino de Idiomas

Um sistema avançado integra entrada de voz/texto com um modelo de linguagem (LLM) multilíngue (inglês e português), suportado por módulos especializados. Em linhas gerais, a arquitetura segue o fluxo   clássico STT   (Speech-to-Text) → LLM → TTS   (Text-to-Speech) .   Cada   bloco   funcional   tem responsabilidade distinta: converter áudio em texto (STT), analisar o texto (analisador lingüístico), gerar respostas (LLM), sintetizar voz (TTS) e orquestrar o fluxo da conversa. Essa abordagem modular facilita a escalabilidade - por exemplo, o motor de STT, o LLM ou o TTS podem ser atualizados ou escalados de forma independente. O orquestrador central coordena esses componentes em tempo real, mantendo o histórico e o contexto da conversa. A figura abaixo ilustra esse pipeline geral: 1 2

## Reconhecimento de Fala (STT)

O módulo de STT funciona como os 'ouvidos' do sistema, captando a voz do aluno e gerando uma transcrição textual .   Para manter a naturalidade da conversa, ele deve ter alta acurácia e baixa latência (idealmente abaixo de 500 ms) .   Modelos de STT modernos (como Whisper ou APIs em nuvem) são otimizados para conversa, incluindo pontuação automática e endpointing inteligente para detectar pausas e o fim da fala .   Além   disso,   precisam   lidar   bem   com   hesitações   e   sotaques característicos de aprendizes. Por exemplo, sistemas avançados usam modelos de transcrição treinados para fala hesitante e não-nativa, evitando penalizar o aluno por pronúncias imperfeitas . O texto resultante segue para o analisador lingüístico, já contendo pontuação e formatação adequadas. 1 3 3 4

## Analisador Linguístico e Memória do Aluno

O analisador lingüístico recebe o texto do STT (ou de entrada direta) e realiza tarefas de NLP como detecção   de   erros,   análise   gramatical   e   extração   de   vocabulário.   Utiliza   por   exemplo   LLMs especializados   (como   Llama2)   para   identificar   incorreções   e   nuances   no   texto   do   aluno .   Esse componente identifica novos vocábulos (não vistos antes) e calcula a dominância de cada palavra conhecida (uma métrica de domínio ou frequência de uso). Cada vocábulo falado é então registrado na memória do aluno: palavras novas são adicionadas com contagem de ocorrências, e erros gramaticais recorrentes são anotados. A memória de longo prazo do aluno armazena seu perfil geral (idioma alvo, objetivos de aprendizagem, preferências), nível estimado (fluência, tamanho de vocabulário, domínio gramatical) e vocabulário ativo com dominâncias. Esse repositório de memória é compartilhado por todos os agentes do sistema e é consultado em tempo real para personalizar respostas . 5 6

## LLM Multilíngue (Resposta Interativa)

O LLM é o 'cérebro' do tutor de IA, recebendo o texto analisado (do STT+analisador) e gerando a resposta. Deve suportar português e inglês, permitindo alternância de idioma conforme o aluno. Ele considera o contexto atual (diálogo recente e metas do aluno) e emite um texto de resposta apropriado. Arquiteturas sofisticadas podem usar múltiplos agentes LLM especializados: por exemplo, um agente de lição (Lesson Agent) conduz o diálogo e incorpora a personalidade de tutor, enquanto um agente de progresso (Student Progress Agent) monitora métricas do aluno (fluência, erros, vocabulário) para atualizar o modelo de estudante . Um agente de planejamento (Learning Planning Agent) então usa 7

essas informações para ajustar o plano de estudos a longo prazo. Todos esses agentes consultam a memória persistente (metas, preferências, erros) para manter a coerência da instrução . Em cada interação, o LLM aplica instruções pedagógicas do motor de ensino - por exemplo, inclui termos alvo selecionados ou corrige construções frasais -, gerando um texto de resposta adaptado ao nível do aluno. 6

## Texto-para-Fala (TTS)

O módulo de TTS converte o texto de resposta do LLM em fala natural, atuando como a 'voz' do tutor. Usam-se sintetizadores de voz neural com qualidade próxima à humana . É essencial baixa latência de síntese (tipicamente &lt;200 ms para o primeiro áudio) e alta naturalidade (MOS&gt;4.0, boa prosódia e emoção) . Várias vozes podem ser disponibilizadas (distintas entonações ou sotaques), sem que isso afete os demais módulos. A fala gerada é reproduzida para o aluno, fechando o turno do diálogo. 8 8

## Orquestrador de Conversação

O orquestrador central coordena todo o fluxo, garantindo que áudio e texto circulem corretamente entre os módulos. Ele detecta o fim da fala do aluno (via processamento de VAD ou pausas) e aciona o STT; em seguida, envia o texto ao LLM e, quando a resposta fica pronta, despacha o TTS. Além disso, gerencia turnos e interrupções: se o aluno interrompe o tutor, a síntese é pausada para processar a nova entrada .   O   orquestrador também mantém o histórico da conversa e contextos de sessão. Pode integrar APIs externas (dicionários, bancos de dados de conhecimento, regras gramaticais), unindo inteligência à resposta. Essa camada de controle é projetada para ser assíncrona e tolerante a latências, permitindo escalonar cada componente - por exemplo, múltiplas instâncias de STT ou LLM sem bloquear a experiência. 9

## Motor Pedagógico, Repetição Espaçada e Conteúdo Adaptativo

O motor pedagógico utiliza a memória do aluno para personalizar as atividades. Um sistema de repetição   espaçada periodicamente   seleciona   itens   de   vocabulário   de   fraco   domínio   ou   pouco praticados .   Em linhas gerais, ele executa três passos: (1) Seleção de palavras: identifica termos raramente usados (baixa dominância) ou com longo intervalo desde a última ocorrência, baseando-se em modelos cognitivos de esquecimento .   (2) Inclusão nos diálogos: elabora instruções ao LLM para incluir esses termos alvo em futuros exercícios ou diálogos (por exemplo, formulando prompts que forçam o uso de certas palavras). (3) Avaliação do progresso: monitora se o aluno começa a usar espontaneamente essas palavras em contextos corretos, indicando retenção. 10 10

Além disso, o motor pedagógico gera conteúdo didático adaptativo conforme o perfil do aluno. Ele produz mini-diálogos contextualizados, reformulações de frases e desafios de expressão focados em pontos fracos detectados. Por exemplo, pode criar roteiros de conversação personalizados sobre tópicos definidos pelo aluno ,   enfatizando vocabulário e estruturas gramaticais que precisam ser reforçados. O LLM gera explicações de erros e fornece feedback corretivo em tempo real. Todo o desempenho do aluno (respostas, erros, sugestões do LLM) é registrado no histórico, permitindo análises posteriores e ajustes contínuos do perfil de aprendizado. 11

Em suma, a arquitetura modular - com STT, analisador, LLM, TTS, orquestrador e motor pedagógico bem separados - garante clareza de responsabilidades e escalabilidade futura. Cada módulo pode ser atualizado (por exemplo, substituir o STT ou adotar um LLM mais potente) sem refazer todo o sistema. Os componentes em nuvem ou em contêineres permitem escalar recursos (processamento de fala, inferência   do   LLM,   banco   de   dados   de   memória)   conforme   cresce   o   número   de   usuários.   Essa

separação disciplinada de funções assegura que o sistema permaneça flexível, atualizável e capaz de evoluir com novas tecnologias de IA.

Fontes: Implementações acadêmicas e comerciais de sistemas de ensino de idiomas por IA . 1 9 12 5 10 7

The voice AI stack for building agents in 2025

https://www.assemblyai.com/blog/the-voice-ai-stack-for-building-agents

Guia Completo do OpenAI TTS: Vozes de IA, API e Casos de Uso em 2025

https://skywork.ai/skypage/pt/openai-tts-voices-api-use-cases/1986254914440462336

Inside Praktika's conversational approach to language learning | OpenAI

https://openai.com/index/praktika/

Building an AI Language Tutor for EdTech - Apriorit

https://www.apriorit.com/dev-blog/building-an-ai-language-tutor

Language Learning Innovation in Student Modelling - Adaptemy

https://www.adaptemy.com/latest-innovations-in-language-learning/

An Intelligent English-Speaking Training System Using Generative AI and Speech Recognition

https://www.mdpi.com/2076-3417/16/1/189
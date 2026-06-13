/**
 * Mock API responses for frontend E2E tests.
 * 
 * Provides pre-defined mock responses for common API endpoints.
 */

export interface MockResponse {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: string | ArrayBuffer | Blob;
}

export interface ConversationSegment {
  text: string;
  lang: 'pt' | 'en';
}

export const mockSpeechResponse: MockResponse = {
  status: 200,
  statusText: 'OK',
  headers: {
    'Content-Type': 'audio/wav',
  },
  body: new Blob([new ArrayBuffer(44)]), // Minimal WAV
};

export const mockTextResponse: MockResponse = {
  status: 200,
  statusText: 'OK',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify([
    { text: 'Olá! Como posso ajudar?', lang: 'pt' },
    { text: 'Hello! How can I help?', lang: 'en' },
  ]),
};

export const mockErrorResponse: MockResponse = {
  status: 500,
  statusText: 'Internal Server Error',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ error: 'Service temporarily unavailable' }),
};

export const mockTimeoutResponse: MockResponse = {
  status: 0,
  statusText: '',
  headers: {},
  body: new Blob(),
};

export function createMockConversation(
  prompt: string,
  segments: ConversationSegment[]
): MockResponse {
  return {
    status: 200,
    statusText: 'OK',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(segments),
  };
}

export function createMockAudioResponse(
  duration: number,
  format: string = 'wav'
): MockResponse {
  return {
    status: 200,
    statusText: 'OK',
    headers: {
      'Content-Type': `audio/${format}`,
      'Content-Length': `${duration * 2}`, // Approximate
    },
    body: new Blob([new ArrayBuffer(duration * 2)]),
  };
}

export class MockService {
  private responses: Map<string, MockResponse> = new Map();

  constructor() {
    this.setDefaultResponses();
  }

  private setDefaultResponses(): void {
    // Default success responses
    this.responses.set('speech', mockSpeechResponse);
    this.responses.set('text', mockTextResponse);
    this.responses.set('error', mockErrorResponse);
  }

  addResponse(endpoint: string, response: MockResponse): void {
    this.responses.set(endpoint, response);
  }

  getResponse(endpoint: string): MockResponse | undefined {
    return this.responses.get(endpoint);
  }

  clearResponses(): void {
    this.responses.clear();
    this.setDefaultResponses();
  }
}

import { NextResponse } from 'next/server';
import { TIDES_SYSTEM_PROMPT } from '@/lib/tidesPrompt';

type Message = {
  role: 'user' | 'model';
  content: string;
};

type GeminiPart = {
  text: string;
};

type GeminiContent = {
  role: 'user' | 'model';
  parts: GeminiPart[];
};

export async function POST(request: Request) {
  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey) {
    return NextResponse.json({ error: 'Missing GEMINI_API_KEY environment variable.' }, { status: 500 });
  }

  let body: { history?: Message[]; playerInput?: string };

  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const { history, playerInput } = body;

  if (!playerInput || !Array.isArray(history)) {
    return NextResponse.json({ error: 'Request body must include history[] and playerInput.' }, { status: 400 });
  }

  const contents: GeminiContent[] = history.map((item) => ({
    role: item.role,
    parts: [{ text: item.content }],
  }));

  contents.push({
    role: 'user',
    parts: [{ text: playerInput }],
  });

  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${encodeURIComponent(apiKey)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        system_instruction: {
          parts: [{ text: TIDES_SYSTEM_PROMPT }],
        },
        contents,
        generation_config: {
          temperature: 0.9,
          topP: 0.95,
          maxOutputTokens: 512,
        },
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    return NextResponse.json({ error: `Gemini API error: ${errorText}` }, { status: 500 });
  }

  const json = await response.json();
  const reply = json?.candidates?.[0]?.content?.parts?.[0]?.text as string | undefined;

  if (!reply) {
    return NextResponse.json({ error: 'No reply received from Gemini.' }, { status: 500 });
  }

  const newHistory: Message[] = [
    ...history,
    { role: 'user', content: playerInput },
    { role: 'model', content: reply },
  ];

  return NextResponse.json({ reply, history: newHistory });
}

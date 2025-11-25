'use client';

import { useEffect, useMemo, useState } from 'react';
import { TIDES_GAME_DESCRIPTION } from '@/lib/tidesPrompt';

type Message = {
  role: 'user' | 'model';
  content: string;
};

const INTRO_PROMPT =
  'Start a fresh loop of *Tides of Remembrance*. Introduce the Waker (he/him) waking near the sea or coastal ruins, hint at his engineering skill, the flooded kingdom, and the mystery of spirits stored in vials. Present the first situation plus options following the required LOCATION/SCENE/OPTIONS/STATS format.';

export default function Home() {
  const [history, setHistory] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const asciiHeader = useMemo(
    () =>
      [
        '   ~~~~~    ~~~~    ~~~~~',
        ' /\\  /\\  /\\/\\  /\\  /\\',
        '|  \\//  ||  \\//  ||  \\//',
        ' \\_/\\_/  \\_/\\_/  \\_/\\_/',
        '   TIDES OF REMEMBRANCE',
      ].join('\n'),
    []
  );

  const sendAction = async (playerInput: string, currentHistory: Message[]) => {
    setLoading(true);
    try {
      const response = await fetch('/api/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: currentHistory, playerInput }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || 'Failed to reach the game API.');
      }

      const data = (await response.json()) as { reply: string; history: Message[] };
      setHistory(data.history);
    } catch (error) {
      console.error(error);
      alert('Something went wrong continuing the story. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (history.length === 0 && !loading) {
      sendAction(INTRO_PROMPT, []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [history.length]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const updatedHistory = [...history, { role: 'user', content: trimmed }];
    setHistory(updatedHistory);
    setInput('');

    await sendAction(trimmed, history);
  };

  return (
    <div className="panel">
      <div className="header">
        <pre aria-hidden className="ascii">{asciiHeader}</pre>
        <h1>Tides of Remembrance – Text Adventure</h1>
        <p className="description">{TIDES_GAME_DESCRIPTION}</p>
      </div>

      <div className="log-area" aria-live="polite">
        {history.length === 0 && !loading && <p>Summoning the tides...</p>}
        {history
          .filter((message) => message.role === 'model')
          .map((message, index) => (
            <div key={index} className="message">
              {message.content}
            </div>
          ))}
        {loading && <p>Waiting for the tides to answer...</p>}
      </div>

      <form className="controls" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Describe your action..."
          disabled={loading}
          aria-label="Player input"
        />
        <button type="submit" disabled={loading}>
          Send
        </button>
      </form>
    </div>
  );
}

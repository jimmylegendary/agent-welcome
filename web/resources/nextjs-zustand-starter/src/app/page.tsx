'use client';

import { useCounterStore } from '../features/counter/counter-store';

export default function HomePage() {
  const count = useCounterStore((state) => state.count);
  const increment = useCounterStore((state) => state.increment);
  const decrement = useCounterStore((state) => state.decrement);

  return (
    <main style={{ maxWidth: 720, margin: '5rem auto', padding: '0 1.5rem' }}>
      <h1>Feature / service / state</h1>
      <p>The counter feature keeps UI, business rules, and Zustand state together.</p>
      <output aria-live="polite">Count: {count}</output>
      <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
        <button type="button" onClick={decrement}>−1</button>
        <button type="button" onClick={increment}>+1</button>
      </div>
    </main>
  );
}

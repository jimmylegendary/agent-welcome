import { create } from 'zustand';
import { addToCount } from './counter-service';

interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
}

export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: addToCount(state.count, 1) })),
  decrement: () => set((state) => ({ count: addToCount(state.count, -1) })),
}));

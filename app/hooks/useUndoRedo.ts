import { useState, useCallback, useRef } from 'react';

export interface UndoRedoState<T> {
  present: T;
  past: T[];
  future: T[];
}

export interface UndoRedoActions<T> {
  canUndo: boolean;
  canRedo: boolean;
  undo: () => void;
  redo: () => void;
  set: (newState: T, description?: string) => void;
  reset: (initialState: T) => void;
  clear: () => void;
}

export interface HistoryEntry<T> {
  state: T;
  description?: string;
  timestamp: Date;
}

const MAX_HISTORY_SIZE = 50; // Limit history to prevent memory issues

export function useUndoRedo<T>(initialState: T): [T, UndoRedoActions<T>] {
  const [state, setState] = useState<UndoRedoState<T>>({
    present: initialState,
    past: [],
    future: []
  });

  const lastActionRef = useRef<string>('');

  const canUndo = state.past.length > 0;
  const canRedo = state.future.length > 0;

  const undo = useCallback(() => {
    if (!canUndo) return;

    setState(prevState => {
      const previous = prevState.past[prevState.past.length - 1];
      const newPast = prevState.past.slice(0, prevState.past.length - 1);

      return {
        past: newPast,
        present: previous,
        future: [prevState.present, ...prevState.future]
      };
    });

    lastActionRef.current = 'undo';
  }, [canUndo]);

  const redo = useCallback(() => {
    if (!canRedo) return;

    setState(prevState => {
      const next = prevState.future[0];
      const newFuture = prevState.future.slice(1);

      return {
        past: [...prevState.past, prevState.present],
        present: next,
        future: newFuture
      };
    });

    lastActionRef.current = 'redo';
  }, [canRedo]);

  const set = useCallback((newState: T, description?: string) => {
    // Skip if the state is the same (deep comparison for objects)
    if (JSON.stringify(state.present) === JSON.stringify(newState)) {
      return;
    }

    // Skip if this is the result of an undo/redo operation
    if (lastActionRef.current === 'undo' || lastActionRef.current === 'redo') {
      lastActionRef.current = '';
      return;
    }

    setState(prevState => {
      // Limit history size
      const newPast = [...prevState.past, prevState.present];
      if (newPast.length > MAX_HISTORY_SIZE) {
        newPast.splice(0, newPast.length - MAX_HISTORY_SIZE);
      }

      return {
        past: newPast,
        present: newState,
        future: [] // Clear future when making a new change
      };
    });

    lastActionRef.current = '';
  }, [state.present]);

  const reset = useCallback((initialState: T) => {
    setState({
      present: initialState,
      past: [],
      future: []
    });
  }, []);

  const clear = useCallback(() => {
    setState(prevState => ({
      present: prevState.present,
      past: [],
      future: []
    }));
  }, []);

  const actions: UndoRedoActions<T> = {
    canUndo,
    canRedo,
    undo,
    redo,
    set,
    reset,
    clear
  };

  return [state.present, actions];
}

// Keyboard shortcut hook for undo/redo
export function useUndoRedoShortcuts<T>(actions: UndoRedoActions<T>) {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.ctrlKey || event.metaKey) {
      if (event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        actions.undo();
      } else if ((event.key === 'z' && event.shiftKey) || event.key === 'y') {
        event.preventDefault();
        actions.redo();
      }
    }
  }, [actions]);

  // Return the handler so components can attach it
  return handleKeyDown;
}

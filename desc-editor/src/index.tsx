import React from 'react';
import ReactDOM from 'react-dom/client';
import { DescDoc, DescEditorRef } from './core/state';
import { DescEditorRoot } from './App';

export type { DescDoc, DescEditorRef } from './core/state';

export const mountDescEditor = async (
  el: HTMLElement,
  initial: Record<'uk' | 'ru' | 'en', DescDoc>
): Promise<DescEditorRef> => {
  const root = ReactDOM.createRoot(el);
  const ref = React.createRef<DescEditorRef>();
  root.render(
    <React.StrictMode>
      <DescEditorRoot ref={ref} initial={initial} />
    </React.StrictMode>
  );

  return new Promise<DescEditorRef>((resolve) => {
    const check = () => {
      if (ref.current) {
        resolve(ref.current);
      } else {
        requestAnimationFrame(check);
      }
    };
    check();
  });
};

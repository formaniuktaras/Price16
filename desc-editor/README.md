# Desc Editor

Модуль «Редактор шаблону опису» для інтеграції у Prom.ua-подібні інтерфейси. Побудований на React + Vite з підтримкою двох режимів (Visual/Code) і Live Preview.

## Запуск демо

```bash
npm install
npm run dev
```

## Підключення як модуля

```ts
import { mountDescEditor } from './src';

const container = document.getElementById('editor');
const initial = {
  uk: { lang: 'uk', html: '<h1>...</h1>', css: '', assets: [] },
  ru: { lang: 'ru', html: '<h1>...</h1>', css: '', assets: [] },
  en: { lang: 'en', html: '<h1>...</h1>', css: '', assets: [] },
};

const ref = await mountDescEditor(container!, initial);

const bundle = ref.toHtmlBundle('uk');
```

### API

```ts
interface DescDoc {
  lang: 'uk' | 'ru' | 'en';
  html: string;
  css: string;
  assets: Array<{ name: string; dataUrl: string }>;
}

interface DescEditorRef {
  getValue(lang?: DescDoc['lang']): DescDoc;
  setValue(doc: DescDoc): void;
  importJson(file: File): Promise<void>;
  exportJson(): Blob;
  toHtmlBundle(lang?: DescDoc['lang']): string;
}
```

## Структура .desc.json

```json
{
  "lang": "uk",
  "html": "<h1>...</h1>",
  "css": "body { ... }",
  "assets": [{ "name": "hero.png", "dataUrl": "data:image/png;base64,..." }],
  "history": [
    { "ts": "2024-01-20T12:00:00.000Z", "html": "...", "css": "..." }
  ],
  "exportedAt": "2024-01-20T12:00:00.000Z"
}
```

## Гарячі клавіші

| Комбінація        | Дія                                   |
| ----------------- | ------------------------------------- |
| `Ctrl + S`        | Зберегти стан в localStorage          |
| `Ctrl + P`        | Відкрити прев'ю                       |
| `Ctrl + Shift + E`| Перемикання Code/Visual               |
| `Ctrl + /`        | Підказка щодо панелі «Шаблони/блоки»  |

## Основні можливості

- CKEditor 5 Classic у Visual Mode з кастомним тулбаром.
- Monaco Editor для HTML/CSS з двома вкладками.
- Live Preview через sandboxed iframe.
- Автозбереження до `localStorage` та експорт/імпорт `.desc.json`.
- Багатомовні вкладки (UA/RU/EN) з окремим станом.
- Панель Assets із drag&drop-файлами та вставкою в HTML.
- Готові блоки (hero, alert, списки, FAQ, таблиця) зі швидким налаштуванням.
- Історія версій (до 25 знімків) з можливістю відкату.

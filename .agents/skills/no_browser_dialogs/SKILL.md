---
name: No Browser Dialogs
description: Never use window.prompt(), window.confirm(), or window.alert() in the UI. Always use inline forms, toast notifications, or custom modal components instead.
---

# No Browser Dialogs — Mandatory Rule

## ❌ Forbidden APIs

The following native browser dialog APIs are **strictly prohibited** in all frontend code:

| API | Why it's banned |
|---|---|
| `window.prompt()` | Ugly native UI, breaks E2E tests (Playwright dialog handling is unreliable), no styling control |
| `window.confirm()` | Same reasons — use a custom confirmation modal or inline buttons instead |
| `window.alert()` | Use toast notifications (e.g. `react-hot-toast`, `sonner`) or inline status banners |

## ✅ Approved Alternatives

### Instead of `window.prompt()` → **Inline Form**

When you need user text input as part of an action:

1. Add a boolean state to toggle the form visibility (e.g. `const [isEditing, setIsEditing] = useState(false)`)
2. Add a string state for the input value (e.g. `const [reason, setReason] = useState('')`)
3. Render an inline `<textarea>` or `<input>` with confirm/cancel buttons
4. Validate input length before enabling the submit button (`disabled={reason.trim().length < 5}`)

**Pattern example (React/TSX):**
```tsx
// State
const [isExpanded, setIsExpanded] = useState(false);
const [inputValue, setInputValue] = useState('');
const [isSubmitting, setIsSubmitting] = useState(false);

// Toggle button
<button onClick={() => setIsExpanded(true)}>Rechazar</button>

// Inline form (shown when isExpanded is true)
{isExpanded && (
    <div className="mt-3 bg-bg-deep p-3 rounded-lg border border-border-dark">
        <label className="text-xs text-text-muted block mb-1">Motivo:</label>
        <textarea
            className="w-full bg-card-dark border border-border-dark rounded-md p-2 text-sm text-white"
            rows={2}
            placeholder="Escriba el motivo aquí..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            autoFocus
        />
        <div className="flex justify-end gap-2 mt-2">
            <button onClick={() => { setIsExpanded(false); setInputValue(''); }}>
                Cancelar
            </button>
            <button
                onClick={handleSubmit}
                disabled={inputValue.trim().length < 5 || isSubmitting}
            >
                {isSubmitting ? 'Enviando...' : 'Confirmar'}
            </button>
        </div>
    </div>
)}
```

### Instead of `window.confirm()` → **Inline Confirmation or Custom Modal**

- For simple yes/no: Use inline buttons with clear labels ("¿Está seguro? [Sí, eliminar] [No, volver]")
- For destructive actions: Use a dedicated confirmation modal component with warning styling

### Instead of `window.alert()` → **Toast Notification or Inline Banner**

- Success messages: Use a toast notification library (`react-hot-toast`, `sonner`)
- Error messages: Use inline error banners within the form/card
- Info messages: Use temporary status banners that auto-dismiss

## 🔍 How to Audit

Search for violations with:
```bash
grep -rn "window\.prompt\|window\.confirm\|window\.alert\|\balert(" --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" src/
```

Note: `alert(` without `window.` is also a violation since it's the same function.

## 📌 E2E Testing Benefit

Inline forms are trivially testable with Playwright:
```ts
// Fill inline textarea
await page.getByPlaceholder('Escriba el motivo aquí...').fill('Mi motivo');
// Click confirm button  
await page.locator('button').filter({ hasText: /confirmar/i }).click();
```

No need for fragile `page.on('dialog')` handlers that frequently fail due to timing issues.

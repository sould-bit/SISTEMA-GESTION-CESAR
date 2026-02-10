/**
 * 🛠️ FORMATTERS - Utilidades de formato para toda la aplicación
 */

/**
 * Formatea un número como moneda colombiana (COP)
 */
export const formatCurrency = (value: number, decimals: number = 0) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

/**
 * Formatea un número con separadores de miles y decimales configurables
 */
export const formatNumber = (value: number, decimals: number = 2) => {
    const safeVal = (value === null || value === undefined || isNaN(value)) ? 0 : value;
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(safeVal);
};

/**
 * Formatea un valor para campos de entrada (input), devolviendo cadena vacía si es null/undefined
 */
export const formatInputValue = (v: any) => {
    if (v === null || v === undefined || v === '') return '';
    const num = typeof v === 'string' ? parseFloat(v.replace(/\./g, '').replace(',', '.')) : v;
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('es-CO').format(num);
};

/**
 * Convierte un número a su representación en palabras (Español)
 * Útil para recibos o documentos legales.
 */
export const numberToWords = (num: number): string => {
    if (num === null || num === undefined || isNaN(num) || num === 0) return 'CERO PESOS';

    const units = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE'];
    const teens = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'];
    const tens = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'];
    const hundreds = ['', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'];

    const roundedNum = Math.round(num);

    if (roundedNum < 0) return 'NÚMERO NEGATIVO';
    if (roundedNum < 10) return units[roundedNum] + ' PESO' + (roundedNum === 1 ? '' : 'S');
    if (roundedNum < 20) return teens[roundedNum - 10] + ' PESOS';

    if (roundedNum < 100) {
        const t = Math.floor(roundedNum / 10);
        const u = roundedNum % 10;
        if (u === 0) return tens[t] + ' PESOS';
        if (t === 2) return 'VEINTI' + units[u].toLowerCase() + ' PESOS';
        return tens[t] + ' Y ' + units[u] + ' PESOS';
    }

    if (roundedNum < 1000) {
        const h = Math.floor(roundedNum / 100);
        const rest = roundedNum % 100;
        if (rest === 0) return (h === 1 ? 'CIEN' : hundreds[h]) + ' PESOS';
        const prefix = h === 1 ? 'CIENTO' : hundreds[h];
        if (rest < 10) return prefix + ' ' + units[rest] + ' PESOS';
        if (rest < 20) return prefix + ' ' + teens[rest - 10] + ' PESOS';
        const t = Math.floor(rest / 10);
        const u = rest % 10;
        if (u === 0) return prefix + ' ' + tens[t] + ' PESOS';
        return prefix + ' ' + tens[t] + ' Y ' + units[u] + ' PESOS';
    }

    if (roundedNum < 1000000) {
        const k = Math.floor(roundedNum / 1000);
        const rest = roundedNum % 1000;
        const kWord = k === 1 ? 'MIL' : numberToWords(k).replace(' PESOS', ' MIL').replace(' PESO', ' MIL');
        if (rest === 0) return kWord + ' PESOS';
        return kWord + ' ' + numberToWords(rest);
    }

    if (roundedNum < 1000000000) {
        const m = Math.floor(roundedNum / 1000000);
        const rest = roundedNum % 1000000;
        const mWord = m === 1 ? 'UN MILLÓN' : numberToWords(m).replace(' PESOS', ' MILLONES').replace(' PESO', ' MILLONES');
        if (rest === 0) return mWord + ' DE PESOS';
        return mWord + ' ' + numberToWords(rest);
    }

    return formatNumber(roundedNum) + ' PESOS';
};

/**
 * Formatea una fecha o timestamp a un formato legible (ej: 05 Feb 2024, 14:30)
 */
export const formatDate = (date: string | Date | undefined): string => {
    if (!date) return '-';

    // Convert string to Date if needed
    const d = typeof date === 'string' ? new Date(date) : date;

    // Verify validity
    if (isNaN(d.getTime())) return 'Fecha inválida';

    return new Intl.DateTimeFormat('es-CO', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    }).format(d);
};

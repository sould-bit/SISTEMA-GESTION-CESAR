/**
 * Tooltip - Reusable tooltip component for field explanations
 */

import { useState, useRef } from 'react';

interface TooltipProps {
    content: string;
    children: React.ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
}

export const Tooltip = ({ content, children, position = 'top' }: TooltipProps) => {
    const [show, setShow] = useState(false);
    const tooltipRef = useRef<HTMLDivElement>(null);

    const positionClasses = {
        top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
        bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
        left: 'right-full top-1/2 -translate-y-1/2 mr-2',
        right: 'left-full top-1/2 -translate-y-1/2 ml-2'
    };

    const arrowClasses = {
        top: 'top-full left-1/2 -translate-x-1/2 border-t-gray-800 border-l-transparent border-r-transparent border-b-transparent',
        bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-800 border-l-transparent border-r-transparent border-t-transparent',
        left: 'left-full top-1/2 -translate-y-1/2 border-l-gray-800 border-t-transparent border-b-transparent border-r-transparent',
        right: 'right-full top-1/2 -translate-y-1/2 border-r-gray-800 border-t-transparent border-b-transparent border-l-transparent'
    };

    return (
        <div className="relative inline-flex items-center">
            <div
                onMouseEnter={() => setShow(true)}
                onMouseLeave={() => setShow(false)}
            >
                {children}
            </div>

            {show && (
                <div
                    ref={tooltipRef}
                    className={`absolute z-50 px-3 py-2 text-xs text-white bg-gray-800 rounded-lg shadow-lg whitespace-normal max-w-xs ${positionClasses[position]}`}
                    style={{ minWidth: '200px' }}
                >
                    {content}
                    <div className={`absolute w-0 h-0 border-4 ${arrowClasses[position]}`} />
                </div>
            )}
        </div>
    );
};

/**
 * HelpIcon - Small ? icon that shows tooltip on hover
 */
export const HelpIcon = ({ text, position = 'top' }: { text: string; position?: 'top' | 'bottom' | 'left' | 'right' }) => (
    <Tooltip content={text} position={position}>
        <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] bg-white/10 text-text-muted rounded-full cursor-help hover:bg-white/20 hover:text-white transition-colors ml-1">
            ?
        </span>
    </Tooltip>
);

export default Tooltip;

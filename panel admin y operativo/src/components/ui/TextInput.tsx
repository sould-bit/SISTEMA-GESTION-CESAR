import { InputHTMLAttributes, forwardRef } from 'react';

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
    label: string;
    icon?: string;
    error?: string;
}

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
    ({ label, icon, error, className, ...props }, ref) => {
        return (
            <div className={`space-y-1.5 group ${className}`}>
                <label className="block text-xs font-semibold text-text-muted uppercase tracking-wider ml-1">
                    {label}
                </label>
                <div className="relative">
                    {icon && (
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <span className="material-symbols-outlined text-text-muted text-[20px] group-focus-within:text-white transition-colors">
                                {icon}
                            </span>
                        </div>
                    )}
                    <input
                        ref={ref}
                        className={`
                            block w-full bg-bg-deep border border-border-dark rounded-lg text-white placeholder-text-muted/50 
                            focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all sm:text-sm py-3
                            ${icon ? 'pl-10 pr-3' : 'px-3'}
                            ${error ? 'border-status-alert focus:border-status-alert focus:ring-status-alert' : ''}
                        `}
                        {...props}
                    />
                </div>
                {error && <span className="text-status-alert text-xs ml-1 flex items-center gap-1"><span className="material-symbols-outlined text-[10px]">error</span>{error}</span>}
            </div>
        );
    }
);

TextInput.displayName = 'TextInput';

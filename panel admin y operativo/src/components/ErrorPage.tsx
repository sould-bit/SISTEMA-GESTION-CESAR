import { useRouteError, isRouteErrorResponse } from "react-router-dom";

export const ErrorPage = () => {
    const error: unknown = useRouteError();
    console.error(error);

    let errorMessage: string;
    let errorStatus: number | undefined;

    if (isRouteErrorResponse(error)) {
        // error is type `ErrorResponse`
        errorMessage = error.statusText || error.data?.message || "Error desconocido";
        errorStatus = error.status;
    } else if (error instanceof Error) {
        errorMessage = error.message;
    } else if (typeof error === 'string') {
        errorMessage = error;
    } else {
        errorMessage = 'Unknown error';
    }

    return (
        <div id="error-page" className="flex flex-col items-center justify-center min-h-screen bg-asphalt text-white p-6 text-center">
            <div className="bg-asphalt-light p-8 rounded-2xl border border-asphalt-lighter shadow-2xl max-w-md w-full">
                <span className="material-symbols-outlined text-6xl text-alert-red mb-4">error</span>
                <h1 className="text-3xl font-bold mb-2">Oops!</h1>
                <p className="text-slate-400 mb-6">Ha ocurrido un error inesperado.</p>

                <div className="bg-asphalt p-4 rounded-lg border border-asphalt-lighter mb-6 text-left overflow-auto max-h-40">
                    <p className="font-mono text-sm text-alert-red">
                        {errorStatus && <span className="font-bold mr-2">[{errorStatus}]</span>}
                        {errorMessage}
                    </p>
                </div>

                <button
                    onClick={() => window.location.href = '/'}
                    className="w-full py-3 px-4 bg-fastops-orange hover:bg-orange-600 rounded-lg text-white font-bold transition-colors"
                >
                    Volver al Inicio
                </button>
            </div>
        </div>
    );
}

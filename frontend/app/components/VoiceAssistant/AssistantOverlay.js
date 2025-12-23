import React, { useState, useEffect, useRef } from 'react';
import { FaMicrophone, FaStop, FaTimes, FaKeyboard, FaPaperPlane } from 'react-icons/fa';
import { useVoiceTransaction } from './useVoiceTransaction';

export default function AssistantOverlay({ onClose }) {
    const { docState, assistantMessage, processVoiceCommand, updateStateManual } = useVoiceTransaction();
    const [transcript, setTranscript] = useState('');
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);

    // Detección de Voz (Simple Speech API)
    useEffect(() => {
        if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
            const recognition = new window.webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'es-ES';
            recognition.interimResults = false;

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                setTranscript(text);
                processVoiceCommand(text); // Ejecutar automáticamente al terminar de hablar
                setIsListening(false);
            };

            recognition.onerror = (event) => {
                console.error("Speech error", event);
                setIsListening(false);
            };

            recognition.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current = recognition;
        }
    }, [processVoiceCommand]);

    const toggleListening = () => {
        if (!recognitionRef.current) return;
        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        } else {
            setTranscript("Escuchando...");
            recognitionRef.current.start();
            setIsListening(true);
        }
    };

    const handleManualSubmit = (e) => {
        e.preventDefault();
        if (!transcript) return;
        processVoiceCommand(transcript);
        setTranscript('');
    }

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
            {/* Main Container */}
            <div className="relative w-full max-w-6xl h-[85vh] bg-white rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row">

                {/* Botón Cerrar */}
                <button onClick={onClose} className="absolute top-4 right-4 z-50 p-2 bg-gray-100 rounded-full hover:bg-gray-200 transition">
                    <FaTimes />
                </button>

                {/* Left: Chat / Conversation */}
                <div className="w-full md:w-1/3 bg-gray-50 flex flex-col border-r border-gray-100">
                    <div className="flex-1 p-6 overflow-y-auto flex flex-col items-center justify-center text-center space-y-6">
                        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
                            <span className="text-3xl">🤖</span>
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">Asistente Contable</h2>

                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 max-w-xs">
                            <p className="text-gray-600 text-lg leading-relaxed">
                                {assistantMessage}
                            </p>
                        </div>

                        {docState.step === 'PROCESSING' && (
                            <div className="flex space-x-2">
                                <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce"></div>
                                <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce delay-75"></div>
                                <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce delay-150"></div>
                            </div>
                        )}
                    </div>

                    {/* Controls */}
                    <div className="p-6 bg-white border-t border-gray-100">
                        {/* Mic Button */}
                        <div className="flex justify-center mb-6">
                            <button
                                onClick={toggleListening}
                                className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl shadow-xl transition-all duration-300 
                                    ${isListening ? 'bg-red-500 text-white animate-pulse scale-110' : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-105'}
                                `}
                            >
                                {isListening ? <FaStop /> : <FaMicrophone />}
                            </button>
                        </div>

                        {/* Text Input Fallback */}
                        <form onSubmit={handleManualSubmit} className="relative">
                            <input
                                type="text"
                                value={transcript === 'Escuchando...' ? '' : transcript}
                                onChange={(e) => setTranscript(e.target.value)}
                                placeholder="O escribe aquí..."
                                className="w-full pl-10 pr-10 py-3 rounded-xl bg-gray-100 border-transparent focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all text-sm"
                            />
                            <FaKeyboard className="absolute left-3 top-3.5 text-gray-400" />
                            <button type="submit" className="absolute right-3 top-3 text-blue-600 hover:text-blue-800">
                                <FaPaperPlane />
                            </button>
                        </form>
                    </div>
                </div>

                {/* Right: Live Preview */}
                <div className="w-full md:w-2/3 bg-gray-100 p-8 overflow-y-auto">
                    <div className="max-w-3xl mx-auto bg-white min-h-[600px] shadow-lg rounded-sm p-10 relative">
                        {/* Paper Effect */}
                        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>

                        {/* Header Documento */}
                        <div className="flex justify-between items-start mb-8 border-b pb-6">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-800 mb-2">
                                    {docState.tipo_documento || "Nuevo Documento"}
                                </h1>
                                <p className="text-sm text-gray-500 uppercase tracking-wider font-semibold">Borrador</p>
                            </div>
                            <div className="text-right">
                                <div className="text-sm text-gray-500">Fecha</div>
                                <div className="text-lg font-medium">{docState.fecha}</div>
                            </div>
                        </div>

                        {/* Tercero */}
                        <div className="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-100">
                            <div className="text-xs text-gray-400 uppercase font-bold mb-1">Tercero / Cliente</div>
                            <div className="text-xl text-gray-800">
                                {docState.tercero ? docState.tercero.nombre : <span className="text-gray-300 italic">-- Sin asignar --</span>}
                            </div>
                        </div>

                        {/* Lines Table */}
                        <table className="w-full mb-8">
                            <thead>
                                <tr className="border-b-2 border-gray-100 text-left">
                                    <th className="py-2 text-sm font-semibold text-gray-600">Cuenta</th>
                                    <th className="py-2 text-sm font-semibold text-gray-600">Detalle</th>
                                    <th className="py-2 text-sm font-semibold text-gray-600 text-right">Débito</th>
                                    <th className="py-2 text-sm font-semibold text-gray-600 text-right">Crédito</th>
                                </tr>
                            </thead>
                            <tbody>
                                {docState.movimientos.length === 0 ? (
                                    <tr>
                                        <td colSpan="4" className="py-12 text-center text-gray-400 italic">
                                            "Agrega líneas diciendo: '100 mil pesos a la Caja General'"
                                        </td>
                                    </tr>
                                ) : (
                                    docState.movimientos.map((mov, idx) => (
                                        <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50">
                                            <td className="py-3 text-gray-800 font-medium">{mov.cuenta_nombre}</td>
                                            <td className="py-3 text-gray-600 text-sm">{mov.concepto}</td>
                                            <td className="py-3 text-right text-gray-800 font-mono">
                                                {mov.debito > 0 ? mov.debito.toLocaleString() : '-'}
                                            </td>
                                            <td className="py-3 text-right text-gray-800 font-mono">
                                                {mov.credito > 0 ? mov.credito.toLocaleString() : '-'}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                            <tfoot className="border-t-2 border-gray-100">
                                <tr>
                                    <td colSpan="2" className="py-4 text-right font-bold text-gray-600">Totales</td>
                                    <td className="py-4 text-right font-bold font-mono text-gray-800">
                                        {docState.total_debito.toLocaleString()}
                                    </td>
                                    <td className="py-4 text-right font-bold font-mono text-gray-800">
                                        {docState.total_credito.toLocaleString()}
                                    </td>
                                </tr>
                                {Math.abs(docState.total_debito - docState.total_credito) > 0 && (
                                    <tr>
                                        <td colSpan="4" className="text-right text-red-500 font-bold text-sm py-2">
                                            Diferencia: {(docState.total_debito - docState.total_credito).toLocaleString()}
                                        </td>
                                    </tr>
                                )}
                            </tfoot>
                        </table>

                        {docState.step === 'SAVING' && (
                            <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
                                <div className="text-center">
                                    <div className="text-4xl animate-bounce mb-4">💾</div>
                                    <h3 className="text-xl font-bold text-gray-800">Guardando documento...</h3>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

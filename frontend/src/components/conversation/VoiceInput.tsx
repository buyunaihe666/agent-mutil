import { useState, useRef, useCallback, useEffect } from "react";
import { Mic, Square } from "lucide-react";

// Web Speech API type declarations (not in standard TS lib)
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
type SpeechRecognitionResult = SpeechRecognitionAlternative[];
type SpeechRecognitionResultList = SpeechRecognitionResult[];
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

interface VoiceInputProps {
  onTranscription: (text: string) => void;
}

export function VoiceInput({ onTranscription }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [interimText, setInterimText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Feature detection
  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setIsSupported(false);
    }
  }, []);

  const stopRecording = useCallback(() => {
    recognitionRef.current?.stop();
    setIsRecording(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const startRecording = useCallback(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) {
      setIsSupported(false);
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = "zh-CN";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0]?.transcript ?? "")
        .join("");
      setInterimText(transcript);
      if (event.results[0]?.[0] && event.results[event.results.length - 1]?.[0]?.confidence > 0) {
        onTranscription(transcript);
        setInterimText("");
        stopRecording();
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessages: Record<string, string> = {
        "no-speech": "未检测到语音",
        "audio-capture": "无法访问麦克风",
        "not-allowed": "麦克风权限被拒绝",
        "network": "网络错误",
      };
      setError(errorMessages[event.error] || `语音识别错误: ${event.error}`);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;
    recognition.start();

    // Auto-stop after 60s
    timeoutRef.current = setTimeout(() => {
      stopRecording();
      setError("录音超时 (60秒)");
    }, 60000);

    setIsRecording(true);
    setError(null);
  }, [onTranscription, stopRecording]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  if (!isSupported) return null;

  return (
    <span
      role="button"
      tabIndex={0}
      title={isRecording ? `录音中... "${interimText}"` : (error ?? "语音输入")}
      className={error ? "text-red-500" : ""}
      onClick={isRecording ? stopRecording : startRecording}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (isRecording) stopRecording(); else startRecording();
        }
      }}
    >
      {isRecording ? (
        <>
          <Square
            aria-hidden="true"
            size={17}
            className="cursor-pointer text-red-500 hover:text-red-700 transition-colors animate-pulse"
          />
          {interimText && (
            <span className="absolute -top-8 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
              {interimText}
            </span>
          )}
        </>
      ) : (
        <Mic
          aria-hidden="true"
          size={17}
          className={`cursor-pointer transition-colors ${
            error
              ? "text-red-400 hover:text-red-600"
              : "text-gray-500 hover:text-blue-600"
          }`}
        />
      )}
    </span>
  );
}

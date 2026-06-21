import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VoiceInput } from "../../../components/conversation/VoiceInput";

// Mock Web Speech API
const mockStart = vi.fn();
const mockStop = vi.fn();

class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = "";
  maxAlternatives = 1;
  onresult: ((event: unknown) => void) | null = null;
  onerror: ((event: unknown) => void) | null = null;
  onend: (() => void) | null = null;
  start = mockStart;
  stop = mockStop;
  abort = vi.fn();
}

describe("VoiceInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    delete (window as Record<string, unknown>).SpeechRecognition;
    delete (window as Record<string, unknown>).webkitSpeechRecognition;
  });

  it("renders mic button when SpeechRecognition is supported", () => {
    (window as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;
    const onTranscription = vi.fn();
    render(<VoiceInput onTranscription={onTranscription} />);
    expect(screen.getByRole("button")).toBeDefined();
  });

  it("renders nothing when SpeechRecognition is not supported", () => {
    const onTranscription = vi.fn();
    const { container } = render(<VoiceInput onTranscription={onTranscription} />);
    expect(container.innerHTML).toBe("");
  });

  it("starts recording on mic button click", () => {
    (window as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;
    const onTranscription = vi.fn();
    render(<VoiceInput onTranscription={onTranscription} />);
    fireEvent.click(screen.getByRole("button"));
    expect(mockStart).toHaveBeenCalledOnce();
  });

  it("stops recording on second click", () => {
    (window as Record<string, unknown>).SpeechRecognition = MockSpeechRecognition;
    const onTranscription = vi.fn();
    render(<VoiceInput onTranscription={onTranscription} />);
    fireEvent.click(screen.getByRole("button")); // start
    expect(mockStart).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button")); // stop
    expect(mockStop).toHaveBeenCalledOnce();
  });

  it("supports webkitSpeechRecognition fallback", () => {
    (window as Record<string, unknown>).webkitSpeechRecognition = MockSpeechRecognition;
    const onTranscription = vi.fn();
    render(<VoiceInput onTranscription={onTranscription} />);
    expect(screen.getByRole("button")).toBeDefined();
  });
});

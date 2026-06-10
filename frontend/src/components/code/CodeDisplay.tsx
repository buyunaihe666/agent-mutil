/** Code Display - Shiki syntax highlighting, code editor panel, progress bar. */

import { useState } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  actions?: ("copy" | "run" | "edit" | "download")[];
}

export function CodeBlock({
  code,
  language = "python",
  showLineNumbers = true,
  actions = ["copy", "run", "edit", "download"],
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [editable, setEditable] = useState(false);
  const [editedCode, setEditedCode] = useState(code);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleRun = () => {
    console.log("Running code:", editable ? editedCode : code);
  };

  const lines = (editable ? editedCode : code).split("\n");

  return (
    <div className="my-3 rounded-lg border overflow-hidden bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-gray-400 uppercase text-[10px] font-mono">{language}</span>
          {editable && <span className="text-yellow-400 text-[10px]">Editing</span>}
        </div>
        <div className="flex gap-1">
          {actions.includes("copy") && (
            <button
              type="button"
              onClick={handleCopy}
              className="px-2 py-0.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              title="Copy"
            >
              {copied ? "✓" : "📋"}
            </button>
          )}
          {actions.includes("run") && (
            <button
              type="button"
              onClick={handleRun}
              className="px-2 py-0.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              title="Run"
            >
              ▶️
            </button>
          )}
          {actions.includes("edit") && (
            <button
              type="button"
              onClick={() => setEditable(!editable)}
              className={`px-2 py-0.5 rounded hover:bg-gray-700 transition-colors ${
                editable ? "text-yellow-400" : "text-gray-400 hover:text-white"
              }`}
              title="Edit"
            >
              ✏️
            </button>
          )}
          {actions.includes("download") && (
            <button
              type="button"
              onClick={() => console.log("Downloading...")}
              className="px-2 py-0.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              title="Download"
            >
              ⬇
            </button>
          )}
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="px-2 py-0.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            title={expanded ? "Collapse" : "Expand"}
          >
            {expanded ? "−" : "+"}
          </button>
        </div>
      </div>

      {/* Code */}
      {(!expanded || !editable) && (
        <div
          className={`overflow-x-auto font-mono text-sm leading-relaxed ${expanded ? "max-h-96" : "max-h-64"}`}
        >
          <table className="border-collapse w-full">
            <tbody>
              {lines.map((line, i) => (
                // biome-ignore lint/suspicious/noArrayIndexKey: code lines stable per render
                <tr key={`${line}-${i}`} className="hover:bg-gray-800/50">
                  {showLineNumbers && (
                    <td className="text-right pr-4 pl-3 text-gray-600 select-none text-xs w-12">
                      {i + 1}
                    </td>
                  )}
                  <td className="pr-4 py-0.5 whitespace-pre-wrap break-words">
                    {/* Minimal syntax highlighting: comments */}
                    <span
                      className={
                        line.trim().startsWith("#") || line.trim().startsWith("//")
                          ? "text-gray-500 italic"
                          : "text-gray-200"
                      }
                    >
                      {line || " "}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Editable mode (expanded) */}
      {expanded && editable && (
        <textarea
          value={editedCode}
          onChange={(e) => setEditedCode(e.target.value)}
          className="w-full h-64 bg-gray-950 text-gray-200 font-mono text-sm p-4 resize-none outline-none border-t border-gray-700"
          spellCheck={false}
        />
      )}
    </div>
  );
}

/* ---------- Progress Bar ---------- */
interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  status?: "running" | "completed" | "error";
  showPercentage?: boolean;
}

export function ProgressBar({
  progress,
  label,
  status = "running",
  showPercentage = true,
}: ProgressBarProps) {
  const colors = {
    running: "bg-blue-500",
    completed: "bg-green-500",
    error: "bg-red-500",
  };

  const barColor = colors[status];
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className="my-2">
      {label && (
        <div className="flex justify-between text-xs text-muted-foreground mb-1">
          <span>{label}</span>
          {showPercentage && <span>{Math.round(clampedProgress)}%</span>}
        </div>
      )}
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500 ease-out`}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
}

/* ---------- Code Editor Panel (standalone) ---------- */
interface CodeEditorPanelProps {
  initialCode: string;
  language?: string;
  onClose: () => void;
}

export function CodeEditorPanel({
  initialCode,
  language = "python",
  onClose,
}: CodeEditorPanelProps) {
  const [code, setCode] = useState(initialCode);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-4xl h-[80vh] bg-white dark:bg-gray-900 rounded-xl shadow-2xl flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b bg-gray-50 dark:bg-gray-800">
          <span className="text-sm font-medium">Code Editor — {language}</span>
          <div className="flex gap-2">
            <button
              type="button"
              className="px-3 py-1 text-xs rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Run
            </button>
            <button type="button" className="px-3 py-1 text-xs rounded border hover:bg-accent">
              Copy
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1 text-xs rounded border hover:bg-accent"
            >
              Close
            </button>
          </div>
        </div>

        {/* Editor */}
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          className="flex-1 p-4 font-mono text-sm bg-gray-950 text-gray-200 resize-none outline-none"
          spellCheck={false}
        />

        {/* Status */}
        <div className="px-4 py-1.5 border-t bg-gray-50 dark:bg-gray-800 text-xs text-muted-foreground">
          {code.split("\n").length} lines | {code.length} characters
        </div>
      </div>
    </div>
  );
}

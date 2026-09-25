import { useState } from "react";
import { Search, GitBranch, Sparkles, Database } from "lucide-react";
import StatusChip from "./StatusChip.jsx";

export default function Sidebar({ onRun, loading, backendStatus }) {
  const [mode, setMode] = useState("sample");
  const [repoInput, setRepoInput] = useState("");
  const [validationError, setValidationError] = useState(null);

  function handleRun() {
    if (mode === "github") {
      if (!repoInput.includes("/")) {
        setValidationError(
          "Enter a repository as owner/repo (e.g. pallets/flask)"
        );
        return;
      }

      setValidationError(null);

      const [owner, repo] = repoInput.split("/", 2);

      onRun({
        mode,
        owner,
        repo,
      });
    } else {
      setValidationError(null);

      onRun({
        mode,
      });
    }
  }

  return (
    <aside
      className="
      w-full
      lg:w-[360px]
      flex-shrink-0

      rounded-[28px]

      bg-[#111113]/80
      backdrop-blur-xl

      border
      border-white/10

      p-7

      shadow-[0_20px_80px_rgba(0,0,0,.45)]
    "
    >
      {/* Header */}

      <div className="mb-8">
        <div
          className="
        w-14
        h-14
        rounded-2xl

        bg-gradient-to-br
        from-cyan-500/20
        to-blue-500/20

        flex
        items-center
        justify-center

        border
        border-cyan-500/20

        mb-5
        "
        >
          <Sparkles className="w-6 h-6 text-cyan-300" />
        </div>

        <p className="font-mono text-[11px] tracking-[0.25em] uppercase text-cyan-400">
          // Repository Analysis
        </p>

        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">
          Analyze Repository
        </h2>

        <p className="text-sm text-textLo mt-3 leading-7">
          Detect behavioural drift using machine learning and AI-powered
          explanations.
        </p>
      </div>

      {/* Scan Type */}

      <div className="space-y-4">

        <button
          onClick={() => setMode("sample")}
          className={`
          w-full
          rounded-2xl
          p-4
          border
          text-left
          transition-all
          duration-300

          ${
            mode === "sample"
              ? "border-blue-500 bg-blue-500/10"
              : "border-white/10 hover:border-white/20 bg-white/[0.02]"
          }
          `}
        >
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-blue-400" />

            <div>
              <div className="font-semibold text-white">
                Sample Dataset
              </div>

              <div className="text-xs text-textLo mt-1">
                Offline • No API required
              </div>
            </div>
          </div>
        </button>

        <button
          onClick={() => setMode("github")}
          className={`
          w-full
          rounded-2xl
          p-4
          border
          text-left
          transition-all
          duration-300

          ${
            mode === "github"
              ? "border-blue-500 bg-blue-500/10"
              : "border-white/10 hover:border-white/20 bg-white/[0.02]"
          }
          `}
        >
          <div className="flex items-center gap-3">
            <GitBranch className="w-5 h-5 text-white" />

            <div>
              <div className="font-semibold text-white">
                GitHub Repository
              </div>

              <div className="text-xs text-textLo mt-1">
                Analyze a live repository
              </div>
            </div>
          </div>
        </button>

      </div>

      {/* Repository Input */}

      {mode === "github" && (
        <div className="mt-7">

          <label className="block text-xs uppercase tracking-[0.18em] text-textLo mb-3">
            Repository
          </label>

          <div
            className="
            flex
            items-center

            rounded-2xl

            border
            border-white/10

            bg-white/[0.03]

            px-4

            transition

            focus-within:border-blue-500
            focus-within:ring-4
            focus-within:ring-blue-500/10
          "
          >
            <Search className="w-4 h-4 text-textLo" />

            <input
              type="text"
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder=" Enter as Owner/Repo"

              className="
              flex-1

              bg-transparent

              py-4

              px-3

              outline-none

              placeholder:text-zinc-500
              "
            />
          </div>

          {validationError && (
            <p className="text-red-400 text-sm mt-3">
              {validationError}
            </p>
          )}
        </div>
      )}

      {/* Button */}

      <button
        onClick={handleRun}
        disabled={loading}
        className="
        mt-8

        w-full

        h-14

        rounded-2xl

        bg-gradient-to-r
        from-blue-600
        via-blue-500
        to-cyan-500

        text-white

        font-semibold

        transition-all
        duration-300

        hover:scale-[1.02]
        hover:shadow-[0_12px_40px_rgba(59,130,246,.35)]

        active:scale-[0.98]

        disabled:opacity-50
        disabled:pointer-events-none
        "
      >
        {loading ? (
          <span className="flex justify-center items-center gap-2">
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Analyzing...
          </span>
        ) : (
          <span className="flex justify-center items-center gap-2">
            Analyze Repository
            <span className="text-lg">→</span>
          </span>
        )}
      </button>

      {/* Footer */}

      <div className="mt-8 border-t border-white/10 pt-6">

        <p className="font-mono uppercase tracking-[0.2em] text-[11px] text-textLo mb-3">
          AI Backend
        </p>


      </div>
    </aside>
  );
}

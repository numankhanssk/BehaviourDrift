export default function Header() {
  return (
    <div className="border-b border-border pb-10 mb-10">

      <div className="font-mono text-[11px] uppercase tracking-[0.28em] text-cyan-400 mb-4">
        // Repository Intelligence Platform
      </div>

      <div className="flex items-start gap-5">

        <div>

          <h1
            className="
            text-6xl
            font-bold
            leading-none
            tracking-[-0.07em]
            bg-gradient-to-br
            from-white
            via-white
            to-[#8CB8FF]
            bg-clip-text
            text-transparent
            "
          >
            BehaviorDrift
          </h1>

          <p
            className="
            mt-5
            max-w-2xl
            text-[17px]
            leading-8
            text-[#9CA3AF]
            "
          >
            Detect repository behavioural drift using machine learning,
            commit intelligence, and AI-powered explanations. Monitor
            engineering patterns, discover anomalies, and understand
            why behavioural changes occur before they become problems.
          </p>

        </div>

      </div>
    </div>
  );
}
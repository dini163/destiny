/**
 * Application root.
 *
 * Scaffold step: renders a branded splash that exercises the Celestial Obsidian
 * tokens (display/body/numeric fonts, gold palette, glass panel component class).
 * The next step replaces this body with the router-mounted global AppShell.
 */
export default function App() {
  return (
    <main className="flex min-h-screen items-center justify-center px-margin">
      <div className="panel-raised px-12 py-10 text-center">
        <p className="label-caps">Astral Observatory</p>
        <h1 className="mt-4 font-display text-5xl font-semibold text-gold-bright text-glow-gold">
          Destiny
        </h1>
        <div className="gold-rule mx-auto my-5 w-40" />
        <p className="font-display text-lg text-ink-variant">跨文明命运测算聚合平台</p>
        <p className="mt-2 text-sm text-ink-muted">前端基座已就绪 · 全局导航与路由构建中</p>
      </div>
    </main>
  );
}

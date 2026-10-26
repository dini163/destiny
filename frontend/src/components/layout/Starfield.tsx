/**
 * Fixed, non-interactive drifting starfield floating above every page.
 *
 * Two parallax layers of tiny stars glide slowly (far layer forward, near layer
 * in reverse), plus one small distant star with a glowing core and two motes
 * circling it. The layer never captures pointer events, so it cannot
 * block chart interaction; pure CSS motion, frozen under `prefers-reduced-motion`.
 */
export function Starfield() {
  return (
    <div className="starfield" aria-hidden="true">
      <div className="starfield-layer starfield-layer--far" />
      <div className="starfield-layer starfield-layer--near" />
      <div className="starfield-star">
        <div className="starfield-star__orbit" />
      </div>
    </div>
  );
}

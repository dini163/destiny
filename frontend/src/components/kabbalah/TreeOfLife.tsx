import type { KabbalahTree, PillarInfo, SephirahNode } from '../../types/kabbalah';
import { TREE_VIEW, coordinateMap, pillarAccent, toView, type Selection } from '../../lib/kabbalah';

interface TreeOfLifeProps {
  /** The full tree map (10 Sephiroth + hidden Daath + 22 paths). */
  tree: KabbalahTree;
  /** Currently selected node, highlighted in the diagram. */
  selection: Selection;
  /** Select a Sephirah or Path by clicking the diagram. */
  onSelect: (selection: Selection) => void;
}

const { minX, minY, width, height, nodeR } = TREE_VIEW;

/** Column x positions by `pillar.side` (mirror the node columns the engine lays out). */
const PILLAR_X: Record<string, number> = { left: 16, middle: 50, right: 84 };
const PILLAR_TOP = 2;
const PILLAR_BOTTOM = 148;
/** viewBox-space padding above the columns reserved for the pillar-name labels. */
const PILLAR_LABEL_Y = -3.2;

const DISPLAY_FONT = "'Noto Serif SC', 'Noto Serif', 'Songti SC', serif";
const GOLD = '#D4AF37';
const GOLD_BRIGHT = '#F5D77F';
const GOLD_SOFT = '#E6C65C';
const INK_VARIANT = '#D0C5AF';
const PARCHMENT = '#F7F3E3';

/**
 * The 生命之树 diagram — an SVG of ten (plus the hidden Daath) glassy Sephirah discs
 * joined by the twenty-two Paths, each labelled with its Hebrew letter.
 *
 * Nodes and paths are clickable to drive the inspector; the accessible keyboard
 * route is the chip index beside the diagram, so the SVG groups stay pointer-only.
 * Every coordinate, colour and letter comes straight from the engine (no mock).
 *
 * Visual layer (Celestial Obsidian): a deep-space nebula ground with a light falling
 * from the crown, three pillar glows labelled from `tree.pillars`, dual-stroke golden
 * paths carrying a letter medallion at the midpoint, and per-node glass discs with an
 * ambient halo. All decorative gradients are derived from engine colours.
 */
export function TreeOfLife({ tree, selection, onSelect }: TreeOfLifeProps) {
  const coords = coordinateMap(tree.sephiroth);
  const selectedId = selection?.id ?? null;
  const crown = tree.sephiroth[0];

  return (
    <svg
      viewBox={`${minX} ${minY} ${width} ${height}`}
      className="h-auto w-full select-none"
      role="img"
      aria-label={`卡巴拉生命之树：${tree.sephirah_count} 原质与 ${tree.path_count} 路径`}
    >
      <defs>
        <radialGradient id="treeNebula" cx="50%" cy="30%" r="80%">
          <stop offset="0%" stopColor="#23273A" stopOpacity="0.9" />
          <stop offset="55%" stopColor="#141824" stopOpacity="0.95" />
          <stop offset="100%" stopColor="#0A0C12" stopOpacity="1" />
        </radialGradient>
        <radialGradient id="crownGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#F5D77F" stopOpacity="0.34" />
          <stop offset="60%" stopColor="#D4AF37" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#D4AF37" stopOpacity="0" />
        </radialGradient>
        {tree.pillars.map((pillar) => (
          <linearGradient
            key={`pillar-${pillar.id}`}
            id={`pillar-${pillar.id}`}
            x1="0" y1="0" x2="0" y2="1"
          >
            <stop offset="0%" stopColor={pillarAccent(pillar.id)} stopOpacity="0.22" />
            <stop offset="100%" stopColor={pillarAccent(pillar.id)} stopOpacity="0.03" />
          </linearGradient>
        ))}
        {[...tree.sephiroth, ...(tree.daath ? [tree.daath] : [])].map((node) => (
          <radialGradient key={`halo-${node.id}`} id={`halo-${node.id}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={node.color} stopOpacity="0.5" />
            <stop offset="100%" stopColor={node.color} stopOpacity="0" />
          </radialGradient>
        ))}
      </defs>

      {/* Deep-space ground with the light source resting on the crown. */}
      <rect x={minX} y={minY} width={width} height={height} fill="url(#treeNebula)" rx={2} />
      {crown ? (
        <circle
          className="kabbalah-crown-glow"
          cx={toView(crown.x, crown.y).vx} cy={toView(crown.x, crown.y).vy} r={26}
          fill="url(#crownGlow)"
        />
      ) : null}

      <PillarGuides pillars={tree.pillars} />

      {/* Paths first, so the discs sit on top of the connecting lines. */}
      {tree.paths.map((path) => {
        const a = coords.get(path.from_sephirah);
        const b = coords.get(path.to_sephirah);
        if (!a || !b) return null;
        const active = selectedId === path.id;
        const mx = (a.vx + b.vx) / 2;
        const my = (a.vy + b.vy) / 2;
        return (
          <g
            key={path.id}
            className="cursor-pointer"
            onClick={() => onSelect({ kind: 'path', id: path.id })}
            aria-hidden="true"
          >
            {/* Glow underlay, then the hairline stroke, then a wide transparent click target.
                Both visible strokes draw themselves in via pathLength-normalised dashes. */}
            <line
              className="kabbalah-path-grow"
              x1={a.vx} y1={a.vy} x2={b.vx} y2={b.vy}
              pathLength={1} strokeDasharray={1} strokeDashoffset={1}
              stroke={GOLD}
              strokeOpacity={active ? 0.28 : 0.1}
              strokeWidth={active ? 3 : 2.6}
              strokeLinecap="round"
              style={{ animationDelay: `${(path.number - 11) * 0.055}s` }}
            />
            <line
              className="kabbalah-path-grow"
              x1={a.vx} y1={a.vy} x2={b.vx} y2={b.vy}
              pathLength={1} strokeDasharray={1} strokeDashoffset={1}
              stroke={active ? GOLD_BRIGHT : GOLD}
              strokeOpacity={active ? 0.95 : 0.42}
              strokeWidth={active ? 1.6 : 1}
              strokeLinecap="round"
              style={{ animationDelay: `${(path.number - 11) * 0.055}s` }}
            />
            <line x1={a.vx} y1={a.vy} x2={b.vx} y2={b.vy} stroke="transparent" strokeWidth={5} />
            {/* Hebrew-letter medallion riding the path midpoint. */}
            <circle
              cx={mx} cy={my} r={2.7}
              fill="#0B0D13" fillOpacity={0.92}
              stroke={active ? GOLD_BRIGHT : GOLD}
              strokeOpacity={active ? 0.9 : 0.35}
              strokeWidth={0.5}
            />
            <text
              x={mx} y={my}
              textAnchor="middle" dominantBaseline="central"
              fontSize={3.4} fontFamily={DISPLAY_FONT}
              fill={active ? GOLD_BRIGHT : GOLD_SOFT}
              style={{ transition: 'fill 120ms ease' }}
            >
              {path.letter}
            </text>
          </g>
        );
      })}

      {/* The hidden Daath node, drawn dashed and dimmer than the ten. */}
      {tree.daath ? (
        <SephirahDisc
          node={tree.daath}
          active={selectedId === tree.daath.id}
          onSelect={onSelect}
        />
      ) : null}

      {tree.sephiroth.map((node) => (
        <SephirahDisc key={node.id} node={node} active={selectedId === node.id} onSelect={onSelect} />
      ))}
    </svg>
  );
}

/** One Sephirah disc: an ambient halo, a tinted glass circle, and its name. */
function SephirahDisc({
  node,
  active,
  onSelect,
}: {
  node: SephirahNode;
  active: boolean;
  onSelect: (selection: Selection) => void;
}) {
  const { vx, vy } = toView(node.x, node.y);
  const hidden = node.is_hidden;
  return (
    <g
      className="kabbalah-node cursor-pointer"
      style={{ animationDelay: `${0.15 + node.y * 0.45}s` }}
      onClick={() => onSelect({ kind: 'sephirah', id: node.id })}
      aria-hidden="true"
    >
      {/* Ambient halo keeps the disc readable over the nebula, breathes, and flares when selected. */}
      <circle
        className={active ? 'kabbalah-halo kabbalah-halo-static' : 'kabbalah-halo'}
        cx={vx} cy={vy} r={nodeR * 2.7}
        fill={`url(#halo-${node.id})`}
        fillOpacity={active ? 0.9 : 0.45}
      />
      {active ? (
        <>
          <circle
            cx={vx} cy={vy} r={nodeR + 2.2}
            fill="none" stroke={GOLD_BRIGHT} strokeOpacity={0.85} strokeWidth={1.1}
          />
          {/* One-shot selection ripple fanning out from the disc. */}
          <circle
            className="kabbalah-ripple"
            cx={vx} cy={vy} r={nodeR + 2.2}
            fill="none" stroke={GOLD_BRIGHT} strokeOpacity={0.6} strokeWidth={1.2}
          />
        </>
      ) : null}
      <circle
        cx={vx} cy={vy} r={nodeR}
        fill={node.color}
        fillOpacity={hidden ? 0.1 : active ? 0.55 : 0.3}
        stroke={active ? GOLD_BRIGHT : node.color}
        strokeOpacity={hidden ? 0.5 : active ? 0.95 : 0.75}
        strokeWidth={active ? 1.6 : 1.1}
        strokeDasharray={hidden ? '2 1.4' : undefined}
        style={{ transition: 'fill-opacity 150ms ease, stroke 150ms ease' }}
      />
      {/* Specular highlight mimicking a glass surface. */}
      <ellipse
        cx={vx - nodeR * 0.32} cy={vy - nodeR * 0.36}
        rx={nodeR * 0.32} ry={nodeR * 0.18}
        fill="#FFFFFF" fillOpacity={hidden ? 0.12 : 0.32}
        transform={`rotate(-28 ${vx - nodeR * 0.32} ${vy - nodeR * 0.36})`}
      />
      <text
        x={vx} y={vy}
        textAnchor="middle" dominantBaseline="central"
        fontSize={4.4} fontWeight={600} fontFamily={DISPLAY_FONT}
        fill={active ? GOLD_BRIGHT : PARCHMENT}
        opacity={hidden ? 0.85 : 1}
        style={{ transition: 'fill 120ms ease' }}
      >
        {hidden ? '✧' : node.number}
      </text>
      <text
        x={vx} y={vy + nodeR + 4.3}
        textAnchor="middle" fontSize={4} fontFamily={DISPLAY_FONT}
        fill={active ? GOLD_BRIGHT : INK_VARIANT}
        stroke="#0A0D15" strokeWidth={1} paintOrder="stroke" strokeLinejoin="round"
        style={{ transition: 'fill 120ms ease' }}
      >
        {node.name_zh}
      </text>
    </g>
  );
}

/**
 * Three vertical pillar glows labelled with the engine's pillar names; each glow
 * fades toward the base so the eye reads the descent from the crown.
 */
function PillarGuides({ pillars }: { pillars: PillarInfo[] }) {
  return (
    <g aria-hidden="true">
      {pillars.map((pillar) => {
        const x = PILLAR_X[pillar.side] ?? 50;
        const accent = pillarAccent(pillar.id);
        return (
          <g key={pillar.id}>
            <line
              className="kabbalah-pillar"
              x1={x} y1={PILLAR_TOP} x2={x} y2={PILLAR_BOTTOM}
              stroke={`url(#pillar-${pillar.id})`}
              strokeWidth={1.2}
            />
            <circle cx={x} cy={0.2} r={1.1} fill={accent} fillOpacity={0.5} />
            <text
              x={x} y={PILLAR_LABEL_Y}
              textAnchor="middle" fontSize={2.8} fontFamily={DISPLAY_FONT}
              letterSpacing={0.6}
              fill={accent} fillOpacity={0.85}
            >
              {pillar.name_zh}
            </text>
          </g>
        );
      })}
    </g>
  );
}

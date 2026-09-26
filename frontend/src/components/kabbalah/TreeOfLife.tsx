import type { KabbalahTree, SephirahNode } from '../../types/kabbalah';
import { TREE_VIEW, coordinateMap, toView, type Selection } from '../../lib/kabbalah';

interface TreeOfLifeProps {
  /** The full tree map (10 Sephiroth + hidden Daath + 22 paths). */
  tree: KabbalahTree;
  /** Currently selected node, highlighted in the diagram. */
  selection: Selection;
  /** Select a Sephirah or Path by clicking the diagram. */
  onSelect: (selection: Selection) => void;
}

const { minX, minY, width, height, nodeR } = TREE_VIEW;

/**
 * The 生命之树 diagram — an SVG of ten (plus the hidden Daath) glassy Sephirah discs
 * joined by the twenty-two Paths, each labelled with its Hebrew letter.
 *
 * Nodes and paths are clickable to drive the inspector; the accessible keyboard
 * route is the chip index beside the diagram, so the SVG groups stay pointer-only.
 * Every coordinate, colour and letter comes straight from the engine (no mock).
 */
export function TreeOfLife({ tree, selection, onSelect }: TreeOfLifeProps) {
  const coords = coordinateMap(tree.sephiroth);
  const selectedId = selection?.id ?? null;

  return (
    <svg
      viewBox={`${minX} ${minY} ${width} ${height}`}
      className="h-auto w-full select-none"
      role="img"
      aria-label={`卡巴拉生命之树：${tree.sephirah_count} 原质与 ${tree.path_count} 路径`}
    >
      <PillarGuides />

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
            <line
              x1={a.vx} y1={a.vy} x2={b.vx} y2={b.vy}
              stroke={active ? '#F5D77F' : '#E8B93C'}
              strokeOpacity={active ? 0.95 : 0.26}
              strokeWidth={active ? 1.9 : 1}
            />
            {/* Wider transparent line = a comfortable click target. */}
            <line x1={a.vx} y1={a.vy} x2={b.vx} y2={b.vy} stroke="transparent" strokeWidth={5} />
            <text
              x={mx} y={my}
              textAnchor="middle" dominantBaseline="central"
              fontSize={active ? 4.4 : 3.6}
              fill={active ? '#F5D77F' : '#B99A4E'}
              stroke="#0a0d15" strokeWidth={1} paintOrder="stroke" strokeLinejoin="round"
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

/** One Sephirah disc: a tinted glass circle, its number, and its Chinese name. */
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
      className="cursor-pointer"
      onClick={() => onSelect({ kind: 'sephirah', id: node.id })}
      aria-hidden="true"
    >
      {active ? <circle cx={vx} cy={vy} r={nodeR + 2.4} fill={node.color} opacity={0.22} /> : null}
      <circle
        cx={vx} cy={vy} r={nodeR}
        fill={node.color}
        fillOpacity={hidden ? 0.1 : active ? 0.46 : 0.24}
        stroke={active ? '#F5D77F' : node.color}
        strokeWidth={active ? 1.9 : 1.3}
        strokeDasharray={hidden ? '2 1.4' : undefined}
        opacity={hidden ? 0.7 : 1}
      />
      <text
        x={vx} y={vy}
        textAnchor="middle" dominantBaseline="central"
        fontSize={4.2} fontWeight={600} fill="#F5EFE0"
      >
        {hidden ? '✧' : node.number}
      </text>
      <text
        x={vx} y={vy + nodeR + 4.2}
        textAnchor="middle" fontSize={3.7}
        fill={active ? '#F5D77F' : '#C9C0AC'}
        stroke="#0a0d15" strokeWidth={0.9} paintOrder="stroke" strokeLinejoin="round"
      >
        {node.name_zh}
      </text>
    </g>
  );
}

/** Three faint vertical guides marking the mercy / equilibrium / severity pillars. */
function PillarGuides() {
  return (
    <g aria-hidden="true" stroke="#E8B93C" strokeOpacity={0.06} strokeWidth={0.6}>
      <line x1={16} y1={2} x2={16} y2={148} />
      <line x1={50} y1={2} x2={50} y2={148} />
      <line x1={84} y1={2} x2={84} y2={148} />
    </g>
  );
}

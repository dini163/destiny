import type { PathNode, SephirahNode } from '../types/kabbalah';

/**
 * Presentation helpers for the 卡巴拉生命之树 page.
 *
 * The Tree is a fixed map, so most of this is geometry + colour: normalised 0-1
 * coordinates from the backend are projected into an SVG viewBox, and the three
 * pillars get a stable accent so nodes, chips and the inspector agree.
 */

/** What is currently selected in the Tree: a Sephirah, a Path, or nothing. */
export type Selection = { kind: 'sephirah'; id: string } | { kind: 'path'; id: string } | null;

/** Pillar accent colours (echo the mercy/severity/equilibrium natures). */
const PILLAR_ACCENT: Record<string, string> = {
  equilibrium: '#E8B93C',
  mercy: '#7FA8E0',
  severity: '#D6384A',
};

/** The accent hex for a pillar id (falls back to the middle-pillar gold). */
export function pillarAccent(pillar: string): string {
  return PILLAR_ACCENT[pillar] ?? '#E8B93C';
}

/** SVG viewBox geometry for the Tree: normalized coordinates keep a tall portrait layout. */
export const TREE_VIEW = {
  /** viewBox left/top offsets give the crown and root room for labels. */
  minX: -11,
  minY: -12,
  width: 122,
  height: 169,
  /** Node disc radius in viewBox units. */
  nodeR: 5.6,
} as const;

/** Project a normalised Sephirah coordinate into viewBox space. */
export function toView(x: number, y: number): { vx: number; vy: number } {
  return { vx: x * 100, vy: y * 150 };
}

/** Build a `number → {vx,vy}` lookup so paths can find their endpoints. */
export function coordinateMap(sephiroth: readonly SephirahNode[]): Map<number, { vx: number; vy: number }> {
  const map = new Map<number, { vx: number; vy: number }>();
  for (const s of sephiroth) {
    map.set(s.number, toView(s.x, s.y));
  }
  return map;
}

interface PathLabelPoint {
  id: string;
  x: number;
  y: number;
  nx: number;
  ny: number;
}

const PATH_LABEL_CLUSTER_RADIUS = 1.5;
const PATH_LABEL_OFFSET_STEP = 8;

/** Keep Hebrew labels apart when multiple paths share the same midpoint. */
export function pathLabelPositions(
  paths: readonly PathNode[],
  sephiroth: readonly SephirahNode[],
): Map<string, { x: number; y: number }> {
  const coords = coordinateMap(sephiroth);
  const points = paths.flatMap((path) => {
    const from = coords.get(path.from_sephirah);
    const to = coords.get(path.to_sephirah);
    if (!from || !to) return [];
    const dx = to.vx - from.vx;
    const dy = to.vy - from.vy;
    const length = Math.hypot(dx, dy) || 1;
    return [{ id: path.id, x: (from.vx + to.vx) / 2, y: (from.vy + to.vy) / 2, nx: -dy / length, ny: dx / length }];
  });

  return spreadCoincidentLabels(points);
}

function spreadCoincidentLabels(points: PathLabelPoint[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const placed = new Set<string>();

  for (const point of points) {
    if (placed.has(point.id)) continue;
    const cluster = points
      .filter(
        (candidate) =>
          !placed.has(candidate.id) &&
          Math.hypot(candidate.x - point.x, candidate.y - point.y) < PATH_LABEL_CLUSTER_RADIUS,
      )
      .sort((a, b) => a.id.localeCompare(b.id));

    cluster.forEach((candidate, index) => {
      const offset = (index - (cluster.length - 1) / 2) * PATH_LABEL_OFFSET_STEP;
      positions.set(candidate.id, {
        x: candidate.x + candidate.nx * offset,
        y: candidate.y + candidate.ny * offset,
      });
      placed.add(candidate.id);
    });
  }

  return positions;
}

/** The default selection when the page first loads (the crown, Kether). */
export const DEFAULT_SELECTION: Selection = { kind: 'sephirah', id: 'sephirah-1' };

/** Resolve the current selection to a Sephirah or Path node for the inspector. */
export function resolveSelection(
  selection: Selection,
  tree: { sephiroth: readonly SephirahNode[]; daath: SephirahNode | null; paths: readonly PathNode[] },
): { kind: 'sephirah'; node: SephirahNode } | { kind: 'path'; node: PathNode } | null {
  if (selection === null) {
    return null;
  }
  if (selection.kind === 'sephirah') {
    const node = tree.sephiroth.find((s) => s.id === selection.id) ?? (tree.daath?.id === selection.id ? tree.daath : undefined);
    return node ? { kind: 'sephirah', node } : null;
  }
  const node = tree.paths.find((p) => p.id === selection.id);
  return node ? { kind: 'path', node } : null;
}

/** A short one-line descriptor of a path, e.g. 王冠 → 智慧 · 愚者. */
export function pathSummary(path: PathNode): string {
  return `${path.from_name_zh} → ${path.to_name_zh} · ${path.tarot_zh}`;
}

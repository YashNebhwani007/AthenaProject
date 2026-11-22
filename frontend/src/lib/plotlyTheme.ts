/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Dark neon Plotly template that melts into the glass containers.
 * Overrides whatever template the backend embedded (it ships `plotly_white`).
 */

export const NEON_COLORWAY = [
  '#00f0ff',
  '#818cf8',
  '#34d399',
  '#fbbf24',
  '#fb7185',
  '#c084fc',
  '#38bdf8',
  '#a3e635',
]

const axis = {
  gridcolor: 'rgba(148, 163, 184, 0.08)',
  zerolinecolor: 'rgba(0, 240, 255, 0.25)',
  linecolor: 'rgba(148, 163, 184, 0.18)',
  tickcolor: 'rgba(148, 163, 184, 0.18)',
  tickfont: { family: 'JetBrains Mono, monospace', size: 10, color: '#7b8798' },
  title: { font: { family: 'Inter, sans-serif', size: 11, color: '#9aa6b8' } },
  automargin: true,
}

export function neonLayout(layout: Record<string, any> = {}): Record<string, any> {
  const { template: _template, title, ...rest } = layout
  void _template
  const titleText = typeof title === 'string' ? title : title?.text
  const merged: Record<string, any> = {
    ...rest,
    autosize: true,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    colorway: NEON_COLORWAY,
    font: { family: 'Inter, sans-serif', color: '#9aa6b8', size: 11 },
    margin: { l: 48, r: 16, t: titleText ? 44 : 16, b: 40 },
    hoverlabel: {
      bgcolor: '#0e121b',
      bordercolor: 'rgba(0, 240, 255, 0.45)',
      font: { family: 'JetBrains Mono, monospace', size: 11, color: '#e6edf7' },
    },
    legend: {
      bgcolor: 'rgba(0,0,0,0)',
      font: { size: 10, color: '#9aa6b8' },
      orientation: 'h',
      y: -0.18,
    },
    xaxis: { ...(rest.xaxis || {}), ...axis, title: { ...axis.title, text: rest.xaxis?.title?.text } },
    yaxis: { ...(rest.yaxis || {}), ...axis, title: { ...axis.title, text: rest.yaxis?.title?.text } },
  }
  if (titleText) {
    merged.title = {
      text: titleText,
      x: 0.01,
      xanchor: 'left',
      font: { family: 'Inter, sans-serif', size: 13, color: '#e6edf7' },
    }
  }
  return merged
}

/** Re-tint traces so backend default colours (e.g. #3B82F6) adopt the neon palette. */
export function neonData(data: any[] = []): any[] {
  return data.map((trace, i) => {
    const color = NEON_COLORWAY[i % NEON_COLORWAY.length]
    const t = { ...trace }
    if (t.type === 'heatmap') {
      t.colorscale = [
        [0, '#f43f5e'],
        [0.5, '#0e121b'],
        [1, '#00f0ff'],
      ]
      t.colorbar = { ...(t.colorbar || {}), tickfont: { color: '#7b8798', size: 10 }, outlinewidth: 0 }
      return t
    }
    t.marker = {
      ...(t.marker || {}),
      color: Array.isArray(t.marker?.color) ? t.marker.color : color,
      line: { color: 'rgba(255,255,255,0.08)', width: 1 },
    }
    if (t.type === 'bar' || t.type === 'histogram') t.marker.opacity = 0.85
    if (t.type === 'scatter') {
      t.marker.size = t.marker.size ?? 6
      t.marker.opacity = 0.7
    }
    if (t.type === 'box') {
      t.line = { color, width: 1.5 }
      t.fillcolor = `${color}22`
    }
    return t
  })
}

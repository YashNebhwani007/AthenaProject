/* eslint-disable @typescript-eslint/no-explicit-any */
import Plotly from 'plotly.js-dist-min'
import React, { useMemo } from 'react'
import createPlotlyComponent from 'react-plotly.js/factory'
import { neonData, neonLayout } from '../lib/plotlyTheme'

// Bind react-plotly to the minified dist bundle (much smaller than full plotly.js).
const Plot = createPlotlyComponent(Plotly)

export interface PlotlySpec {
  data?: any[]
  layout?: Record<string, any>
}

const PlotlyChart: React.FC<{ spec: PlotlySpec; height?: number }> = ({ spec, height = 320 }) => {
  const data = useMemo(() => neonData(spec.data), [spec.data])
  const layout = useMemo(() => neonLayout(spec.layout), [spec.layout])
  return (
    <Plot
      data={data}
      layout={layout}
      config={{ responsive: true, displayModeBar: false, displaylogo: false }}
      useResizeHandler
      style={{ width: '100%', height }}
    />
  )
}

export default PlotlyChart

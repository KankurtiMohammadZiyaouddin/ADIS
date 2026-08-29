import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

/**
 * RiskChart — doughnut chart for verdict distribution.
 * When fakeCount + realCount > 0, uses real data from props.
 * Falls back to demo data when no analyses have run.
 */
export default function RiskChart({ fakeCount = 0, realCount = 0 }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  const hasData = fakeCount + realCount > 0;

  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');

    const colorFake = '#ba1a1a';   // error — fake
    const colorReal = '#0037b0';   // primary — real
    const colorDemo = '#5e4bc0';   // secondary — demo placeholder

    const labels = hasData ? ['Deepfakes (FAKE)', 'Authentic (REAL)'] : ['High Risk', 'Medium Risk', 'Low Risk'];
    const data   = hasData ? [fakeCount, realCount]                   : [15, 35, 50];
    const colors = hasData ? [colorFake, colorReal]                   : [colorFake, colorDemo, colorReal];

    chartRef.current = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderWidth: 0,
          hoverOffset: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '75%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              usePointStyle: true,
              boxWidth: 6,
              color: '#c4c7c5',
              font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
            },
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw}`,
            },
          },
        },
      },
    });

    return () => chartRef.current?.destroy();
  }, [fakeCount, realCount]);   // re-render when data changes

  return <canvas ref={canvasRef} />;
}

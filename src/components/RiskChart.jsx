import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function RiskChart() {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');

    const colorHigh = '#ba1a1a'; // error
    const colorMedium = '#5e4bc0'; // secondary
    const colorLow = '#0037b0'; // primary

    chartRef.current = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['High Risk', 'Medium Risk', 'Low Risk'],
        datasets: [
          {
            data: [15, 35, 50],
            backgroundColor: [colorHigh, colorMedium, colorLow],
            borderWidth: 0,
            hoverOffset: 4,
          },
        ],
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
              font: {
                family: "'IBM Plex Sans', sans-serif",
                size: 11,
              },
            },
          },
        },
      },
    });

    return () => chartRef.current?.destroy();
  }, []);

  return <canvas ref={canvasRef} />;
}


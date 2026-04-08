<script lang="ts">
	import type { BacktestResult } from '$lib/api';

	interface ChartDataPoint {
		timestamp: string;
		value: number;
	}

	interface Props {
		results: BacktestResult | null;
		signals?: Array<{ created_at: string; signal_type: string; price: number }>;
		height?: number;
	}

	let { results, signals = [], height = 300 }: Props = $props();

	let width = $state(800);
	let containerEl: HTMLDivElement;

	$effect(() => {
		if (containerEl) {
			width = containerEl.clientWidth;
		}
	});

	function generatePortfolioCurve(): ChartDataPoint[] {
		if (!results || signals.length === 0) return [];
		
		const points: ChartDataPoint[] = [];
		const startValue = 10000;
		let currentValue = startValue;
		
		const sortedSignals = [...signals].sort(
			(a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
		);
		
		points.push({
			timestamp: sortedSignals[0]?.created_at || new Date().toISOString(),
			value: currentValue
		});
		
		for (const signal of sortedSignals) {
			if (signal.signal_type === 'buy') {
				currentValue *= 1.05;
			} else if (signal.signal_type === 'sell') {
				currentValue *= 0.95;
			}
			points.push({
				timestamp: signal.created_at,
				value: currentValue
			});
		}
		
		return points;
	}

	function getChartArea(w: number, h: number): { x: number; y: number; width: number; height: number } {
		const padding = { top: 20, right: 20, bottom: 40, left: 60 };
		return {
			x: padding.left,
			y: padding.top,
			width: w - padding.left - padding.right,
			height: h - padding.top - padding.bottom
		};
	}

	function getValueRange(pts: ChartDataPoint[]): { min: number; max: number } {
		if (pts.length === 0) return { min: 0, max: 10000 };
		const values = pts.map(p => p.value);
		const min = Math.min(...values);
		const max = Math.max(...values);
		const padding = (max - min) * 0.1 || 1000;
		return { min: min - padding, max: max + padding };
	}

	function getPointPosition(point: ChartDataPoint, index: number, total: number, area: { x: number; y: number; width: number; height: number }, range: { min: number; max: number }): { x: number; y: number } {
		const x = area.x + (index / Math.max(total - 1, 1)) * area.width;
		const normalizedValue = (point.value - range.min) / (range.max - range.min);
		const y = area.y + area.height - normalizedValue * area.height;
		return { x, y };
	}

	function getYAxisLabels(area: { x: number; y: number; width: number; height: number }, range: { min: number; max: number }): Array<{ value: number; y: number }> {
		const step = (range.max - range.min) / 4;
		return [0, 1, 2, 3, 4].map(i => ({
			value: range.max - i * step,
			y: area.y + (i / 4) * area.height
		}));
	}

	function getXAxisLabels(pts: ChartDataPoint[], area: { x: number; y: number; width: number; height: number }, range: { min: number; max: number }): Array<{ label: string; x: number }> {
		if (pts.length === 0) return [];
		const step = Math.max(1, Math.floor(pts.length / 5));
		return pts
			.filter((_, i) => i % step === 0 || i === pts.length - 1)
			.map((p, i, arr) => ({
				label: new Date(p.timestamp).toLocaleDateString(),
				x: getPointPosition(p, pts.indexOf(p), pts.length, area, range).x
			}));
	}

	function getReturnColor(): string {
		if (!results) return '#888';
		return results.total_return >= 0 ? '#22c55e' : '#ef4444';
	}

	let points = $derived(generatePortfolioCurve());
	let area = $derived(getChartArea(width, height));
	let range = $derived(getValueRange(points));
	let yAxisLabels = $derived(getYAxisLabels(area, range));
	let xAxisLabels = $derived(getXAxisLabels(points, area, range));
</script>

<div class="backtest-chart" bind:this={containerEl}>
	{#if !results}
		<div class="empty-state">
			<p>No backtest results to display</p>
		</div>
	{:else}
		<div class="chart-header">
			<div class="metric">
				<span class="metric-label">Total Return</span>
				<span class="metric-value" style="color: {getReturnColor()}">
					{results.total_return >= 0 ? '+' : ''}{results.total_return.toFixed(2)}%
				</span>
			</div>
			<div class="metric">
				<span class="metric-label">Win Rate</span>
				<span class="metric-value">{results.win_rate.toFixed(1)}%</span>
			</div>
			<div class="metric">
				<span class="metric-label">Total Trades</span>
				<span class="metric-value">{results.total_trades}</span>
			</div>
			<div class="metric">
				<span class="metric-label">Sharpe Ratio</span>
				<span class="metric-value">{results.sharpe_ratio.toFixed(2)}</span>
			</div>
		</div>

		<svg {width} {height} viewBox="0 0 {width} {height}">
			<defs>
				<linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="rgba(102, 126, 234, 0.4)" />
					<stop offset="100%" stop-color="rgba(102, 126, 234, 0)" />
				</linearGradient>
			</defs>

			<g class="grid-lines">
				{#each [0, 1, 2, 3, 4] as i}
					{@const y = area.y + (i / 4) * area.height}
					<line
						x1={area.x}
						y1={y}
						x2={area.x + area.width}
						y2={y}
						stroke="rgba(255,255,255,0.08)"
						stroke-dasharray="4,4"
					/>
				{/each}
			</g>

			<g class="y-axis">
				{#each yAxisLabels as label}
					<text x={area.x - 8} y={label.y + 4} class="axis-label" text-anchor="end">
						${label.value.toLocaleString()}
					</text>
				{/each}
			</g>

			<g class="x-axis">
				{#each xAxisLabels as label}
					<text x={label.x} y={height - 8} class="axis-label" text-anchor="middle">
						{label.label}
					</text>
				{/each}
			</g>

			{#if points.length > 1}
				<path
					d={points.map((p, i) => {
						const pos = getPointPosition(p, i, points.length, area, range);
						if (i === 0) {
							return `M ${pos.x} ${area.y + area.height} L ${pos.x} ${pos.y}`;
						}
						return `L ${pos.x} ${pos.y}`;
					}).join(' ') + ` L ${getPointPosition(points[points.length - 1], points.length - 1, points.length, area, range).x} ${area.y + area.height} Z`}
					fill="url(#portfolioGradient)"
				/>

				<path
					d={points.map((p, i) => {
						const pos = getPointPosition(p, i, points.length, area, range);
						return `${i === 0 ? 'M' : 'L'} ${pos.x} ${pos.y}`;
					}).join(' ')}
					fill="none"
					stroke="#667eea"
					stroke-width="2.5"
				/>
			{/if}
		</svg>

		<div class="chart-footer">
			<div class="stat">
				<span class="stat-label">Buy Signals</span>
				<span class="stat-value buy">{results.buy_signals}</span>
			</div>
			<div class="stat">
				<span class="stat-label">Sell Signals</span>
				<span class="stat-value sell">{results.sell_signals}</span>
			</div>
			<div class="stat">
				<span class="stat-label">Max Drawdown</span>
				<span class="stat-value negative">-{results.max_drawdown.toFixed(2)}%</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.backtest-chart {
		width: 100%;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
		box-sizing: border-box;
	}

	.empty-state {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 300px;
		color: #666;
	}

	.chart-header {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		text-align: center;
	}

	.metric-label {
		font-size: 0.75rem;
		color: #888;
		text-transform: uppercase;
	}

	.metric-value {
		font-size: 1.25rem;
		font-weight: 600;
	}

	svg {
		display: block;
		width: 100%;
		height: auto;
	}

	.axis-label {
		font-size: 10px;
		fill: #666;
	}

	.chart-footer {
		display: flex;
		justify-content: center;
		gap: 2rem;
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}

	.stat-label {
		font-size: 0.75rem;
		color: #888;
	}

	.stat-value {
		font-size: 1rem;
		font-weight: 500;
	}

	.buy {
		color: #22c55e;
	}

	.sell {
		color: #ef4444;
	}

	.negative {
		color: #ef4444;
	}
</style>
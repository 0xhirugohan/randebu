<script lang="ts">
	import type { Signal } from '$lib/api';

	interface Props {
		signals: Signal[];
		height?: number;
	}

	let { signals, height = 200 }: Props = $props();

	let width = $state(800);
	let containerEl: HTMLDivElement;

	$effect(() => {
		if (containerEl) {
			width = containerEl.clientWidth;
		}
	});

	function getSignalPosition(signal: Signal, index: number, total: number): { x: number; y: number } {
		const padding = 30;
		const chartWidth = width - padding * 2;
		const chartHeight = height - padding * 2;
		const x = padding + (index / Math.max(total - 1, 1)) * chartWidth;
		const priceRange = getPriceRange();
		const normalizedPrice = priceRange.min === priceRange.max ? 0.5 : 
			(signal.price - priceRange.min) / (priceRange.max - priceRange.min);
		const y = padding + (1 - normalizedPrice) * chartHeight;
		return { x, y };
	}

	function getPriceRange(): { min: number; max: number } {
		if (signals.length === 0) return { min: 0, max: 1 };
		const prices = signals.map(s => s.price);
		const min = Math.min(...prices);
		const max = Math.max(...prices);
		const padding = (max - min) * 0.1 || 1;
		return { min: min - padding, max: max + padding };
	}

	function getSignalColor(signal: Signal): string {
		switch (signal.signal_type) {
			case 'buy': return '#22c55e';
			case 'sell': return '#ef4444';
			case 'hold': return '#fbbf24';
			default: return '#888';
		}
	}

	function getYAxisLabels(): string[] {
		const range = getPriceRange();
		const step = (range.max - range.min) / 4;
		return [
			range.max.toFixed(6),
			(range.max - step).toFixed(6),
			(range.min + step).toFixed(6),
			range.min.toFixed(6)
		];
	}

	function getXAxisLabels(): string[] {
		if (signals.length === 0) return [];
		const step = Math.max(1, Math.floor(signals.length / 5));
		const labels: string[] = [];
		for (let i = 0; i < signals.length; i += step) {
			labels.push(new Date(signals[i].created_at).toLocaleTimeString());
		}
		return labels;
	}
</script>

<div class="signal-chart" bind:this={containerEl}>
	{#if signals.length === 0}
		<div class="empty-state">
			<p>No signals to display</p>
		</div>
	{:else}
		<svg {width} {height} viewBox="0 0 {width} {height}">
			<defs>
				<linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="rgba(102, 126, 234, 0.3)" />
					<stop offset="100%" stop-color="rgba(102, 126, 234, 0)" />
				</linearGradient>
			</defs>

			<g class="grid-lines">
				{#each [0, 1, 2, 3] as i}
					{@const y = 30 + (i / 3) * (height - 60)}
					<line 
						x1="30" y1={y} 
						x2={width - 30} y2={y}
						stroke="rgba(255,255,255,0.1)"
						stroke-dasharray="4,4"
					/>
				{/each}
			</g>

			<g class="y-axis">
				{#each getYAxisLabels() as label, i}
					{@const y = 30 + (i / 3) * (height - 60)}
					<text x="25" y={y + 4} class="axis-label" text-anchor="end">${label}</text>
				{/each}
			</g>

			<g class="x-axis">
				{#each getXAxisLabels() as label, i}
					{@const x = 30 + (i / (getXAxisLabels().length - 1 || 1)) * (width - 60)}
					<text x={x} y={height - 8} class="axis-label" text-anchor="middle">{label}</text>
				{/each}
			</g>

			<path
				d={signals.map((s, i) => {
					const pos = getSignalPosition(s, i, signals.length);
					return `${i === 0 ? 'M' : 'L'} ${pos.x} ${pos.y}`;
				}).join(' ')}
				fill="none"
				stroke="#667eea"
				stroke-width="2"
			/>

			{#each signals as signal, i}
				{@const pos = getSignalPosition(signal, i, signals.length)}
				{@const color = getSignalColor(signal)}
				<circle
					cx={pos.x}
					cy={pos.y}
					r="6"
					fill={color}
					stroke={color}
					stroke-width="2"
					class="signal-dot"
				>
					<title>{signal.signal_type.toUpperCase()} - ${signal.price.toFixed(6)} - {new Date(signal.created_at).toLocaleString()}</title>
				</circle>
			{/each}
		</svg>

		<div class="legend">
			<div class="legend-item">
				<span class="legend-dot buy"></span>
				<span>Buy</span>
			</div>
			<div class="legend-item">
				<span class="legend-dot sell"></span>
				<span>Sell</span>
			</div>
			<div class="legend-item">
				<span class="legend-dot hold"></span>
				<span>Hold</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.signal-chart {
		width: 100%;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		box-sizing: border-box;
	}

	.empty-state {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 200px;
		color: #666;
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

	.signal-dot {
		cursor: pointer;
		transition: r 0.2s;
	}

	.signal-dot:hover {
		r: 8;
	}

	.legend {
		display: flex;
		justify-content: center;
		gap: 1.5rem;
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		color: #888;
	}

	.legend-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
	}

	.legend-dot.buy {
		background: #22c55e;
	}

	.legend-dot.sell {
		background: #ef4444;
	}

	.legend-dot.hold {
		background: #fbbf24;
	}
</style>
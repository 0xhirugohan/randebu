<script lang="ts">
	import type { Signal } from '$lib/api';
	import { onMount } from 'svelte';

	interface Props {
		signals?: Signal[];
		klines?: { time: number; close: number }[];
		height?: number;
	}

	let { signals = [], klines = [], height = 200 }: Props = $props();

	let width = $state(800);
	let containerEl: HTMLDivElement;
	let canvasEl: HTMLCanvasElement;

	onMount(() => {
		if (containerEl) {
			width = containerEl.clientWidth;
			drawChart();
		}
	});

	$effect(() => {
		if (canvasEl && (signals.length > 0 || klines.length > 0)) {
			drawChart();
		}
	});

	function drawChart() {
		if (!canvasEl) return;
		
		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;

		const dpr = window.devicePixelRatio || 1;
		canvasEl.width = width * dpr;
		canvasEl.height = height * dpr;
		ctx.scale(dpr, dpr);

		// Clear
		ctx.clearRect(0, 0, width, height);

		// Get price data
		const prices = klines.length > 0 
			? klines.map(k => k.close)
			: signals.map(s => s.price);
		
		if (prices.length === 0) return;

		const padding = { top: 20, right: 20, bottom: 30, left: 60 };
		const chartWidth = width - padding.left - padding.right;
		const chartHeight = height - padding.top - padding.bottom;

		// Price range with padding
		const minPrice = Math.min(...prices);
		const maxPrice = Math.max(...prices);
		const priceRange = maxPrice - minPrice || 1;
		const paddedMin = minPrice - priceRange * 0.1;
		const paddedMax = maxPrice + priceRange * 0.1;

		function priceToY(price: number): number {
			return padding.top + (1 - (price - paddedMin) / (paddedMax - paddedMin)) * chartHeight;
		}

		function indexToX(index: number): number {
			return padding.left + (index / (prices.length - 1 || 1)) * chartWidth;
		}

		// Draw grid lines
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
		ctx.lineWidth = 1;
		for (let i = 0; i <= 4; i++) {
			const y = padding.top + (i / 4) * chartHeight;
			ctx.beginPath();
			ctx.moveTo(padding.left, y);
			ctx.lineTo(width - padding.right, y);
			ctx.stroke();
		}

		// Draw Y axis labels
		ctx.fillStyle = '#666';
		ctx.font = '10px monospace';
		ctx.textAlign = 'right';
		for (let i = 0; i <= 4; i++) {
			const price = paddedMax - (i / 4) * (paddedMax - paddedMin);
			const y = padding.top + (i / 4) * chartHeight + 4;
			ctx.fillText('$' + price.toFixed(6), padding.left - 5, y);
		}

		// Draw price line
		ctx.beginPath();
		ctx.strokeStyle = '#667eea';
		ctx.lineWidth = 2;
		for (let i = 0; i < prices.length; i++) {
			const x = indexToX(i);
			const y = priceToY(prices[i]);
			if (i === 0) ctx.moveTo(x, y);
			else ctx.lineTo(x, y);
		}
		ctx.stroke();

		// Fill area under line
		ctx.lineTo(indexToX(prices.length - 1), padding.top + chartHeight);
		ctx.lineTo(indexToX(0), padding.top + chartHeight);
		ctx.closePath();
		const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
		gradient.addColorStop(0, 'rgba(102, 126, 234, 0.2)');
		gradient.addColorStop(1, 'rgba(102, 126, 234, 0)');
		ctx.fillStyle = gradient;
		ctx.fill();

		// Draw signal markers
		if (signals.length > 0) {
			// Draw line to each signal point
			signals.forEach((signal) => {
				const signalIndex = klines.length > 0 
					? klines.findIndex(k => Math.abs(k.close - signal.price) < 0.0001)
					: signals.indexOf(signal);
				
				if (signalIndex >= 0) {
					const x = indexToX(signalIndex);
					const y = priceToY(signal.price);

					// Vertical line from top
					ctx.beginPath();
					ctx.strokeStyle = signal.signal_type === 'buy' ? '#22c55e' : '#ef4444';
					ctx.setLineDash([4, 4]);
					ctx.moveTo(x, padding.top);
					ctx.lineTo(x, y);
					ctx.stroke();
					ctx.setLineDash([]);

					// Signal dot
					ctx.beginPath();
					ctx.arc(x, y, 6, 0, Math.PI * 2);
					ctx.fillStyle = signal.signal_type === 'buy' ? '#22c55e' : '#ef4444';
					ctx.fill();
					ctx.strokeStyle = '#fff';
					ctx.lineWidth = 2;
					ctx.stroke();
				}
			});
		}

		// Legend
		if (signals.length > 0) {
			const buyCount = signals.filter(s => s.signal_type === 'buy').length;
			const sellCount = signals.filter(s => s.signal_type === 'sell').length;

			ctx.fillStyle = '#888';
			ctx.font = '12px sans-serif';
			ctx.textAlign = 'center';
			ctx.fillText(`📈 ${buyCount} Buy | ${sellCount} Sell | ${prices.length} Candles`, width / 2, height - 8);
		} else if (klines.length > 0) {
			ctx.fillStyle = '#888';
			ctx.font = '12px sans-serif';
			ctx.textAlign = 'center';
			ctx.fillText(`${prices.length} Candles (No signals generated)`, width / 2, height - 8);
		}
	}
</script>

<div class="signal-chart" bind:this={containerEl}>
	{#if signals.length === 0 && klines.length === 0}
		<div class="empty-state">
			<p>No data to display. Start a simulation to see price movements.</p>
		</div>
	{:else}
		<canvas 
			bind:this={canvasEl} 
			style="width: {width}px; height: {height}px;"
		></canvas>
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
		text-align: center;
		padding: 1rem;
	}

	canvas {
		display: block;
	}
</style>

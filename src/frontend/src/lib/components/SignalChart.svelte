<script lang="ts">
	import type { Signal } from '$lib/api';
	import { onMount, tick } from 'svelte';

	interface Props {
		signals?: Signal[];
		klines?: { time: number; close: number }[];
		height?: number;
	}

	let { signals = [], klines = [], height = 200 }: Props = $props();

	let width = $state(800);
	let containerEl: HTMLDivElement;
	let canvasEl: HTMLCanvasElement;
	let initialized = $state(false);

	onMount(() => {
		// Set initial width
		if (containerEl) {
			width = containerEl.clientWidth;
		}
		
		// Resize observer
		const resizeObserver = new ResizeObserver(entries => {
			for (const entry of entries) {
				width = entry.contentRect.width;
				drawChart();
			}
		});
		
		if (containerEl) {
			resizeObserver.observe(containerEl);
		}
		
		initialized = true;
		
		return () => {
			resizeObserver.disconnect();
		};
	});

	// Draw when data changes
	$effect(() => {
		// Access reactive values to trigger effect
		const currentSignals = signals;
		const currentKlines = klines;
		const currentWidth = width;
		
		// Wait for DOM to be ready
		tick().then(() => {
			drawChart();
		});
	});

	function drawChart() {
		if (!canvasEl) {
			return;
		}
		
		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;

		const dpr = window.devicePixelRatio || 1;
		canvasEl.width = width * dpr;
		canvasEl.height = height * dpr;
		ctx.scale(dpr, dpr);

		// Clear canvas
		ctx.clearRect(0, 0, width, height);

		// Check if we have data
		if (klines.length === 0 && signals.length === 0) {
			return;
		}

		// Get price data
		let priceData: { time: number; price: number }[] = [];
		
		if (klines.length > 0) {
			priceData = klines.map(k => ({
				time: k.time,
				price: typeof k.close === 'string' ? parseFloat(k.close) : k.close
			})).filter(d => !isNaN(d.price) && d.price > 0);
		} else if (signals.length > 0) {
			priceData = signals.map(s => ({ time: 0, price: s.price }));
		}
		
		if (priceData.length === 0) return;

		const prices = priceData.map(d => d.price);
		const padding = { top: 20, right: 20, bottom: 45, left: 60 };  // More bottom padding for time labels
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
			return padding.left + (index / Math.max(prices.length - 1, 1)) * chartWidth;
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
		ctx.fillStyle = '#888';
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
		ctx.moveTo(indexToX(0), priceToY(prices[0]));
		for (let i = 1; i < prices.length; i++) {
			ctx.lineTo(indexToX(i), priceToY(prices[i]));
		}
		ctx.stroke();

		// Fill area under line
		ctx.lineTo(indexToX(prices.length - 1), padding.top + chartHeight);
		ctx.lineTo(indexToX(0), padding.top + chartHeight);
		ctx.closePath();
		const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
		gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
		gradient.addColorStop(1, 'rgba(102, 126, 234, 0)');
		ctx.fillStyle = gradient;
		ctx.fill();

		// Draw signal markers
		if (signals.length > 0) {
			signals.forEach((signal) => {
				// Find closest price match
				const signalPrice = signal.price;
				let closestIndex = 0;
				let closestDiff = Infinity;
				
				for (let i = 0; i < priceData.length; i++) {
					const diff = Math.abs(priceData[i].price - signalPrice);
					if (diff < closestDiff) {
						closestDiff = diff;
						closestIndex = i;
					}
				}
				
				const x = indexToX(closestIndex);
				const y = priceToY(signalPrice);
				const color = signal.signal_type === 'buy' ? '#22c55e' : '#ef4444';

				// Vertical dashed line
				ctx.beginPath();
				ctx.strokeStyle = color;
				ctx.setLineDash([4, 4]);
				ctx.moveTo(x, padding.top);
				ctx.lineTo(x, y);
				ctx.stroke();
				ctx.setLineDash([]);

				// Signal dot
				ctx.beginPath();
				ctx.arc(x, y, 6, 0, Math.PI * 2);
				ctx.fillStyle = color;
				ctx.fill();
				ctx.strokeStyle = '#fff';
				ctx.lineWidth = 2;
				ctx.stroke();
			});
		}

		// Draw X axis time labels
		ctx.fillStyle = '#666';
		ctx.font = '9px monospace';
		ctx.textAlign = 'center';
		
		const numTimeLabels = Math.min(5, priceData.length);
		for (let i = 0; i < numTimeLabels; i++) {
			const dataIndex = Math.floor(i * (priceData.length - 1) / (numTimeLabels - 1 || 1));
			const x = indexToX(dataIndex);
			
			// Convert timestamp to readable time
			let timeLabel = '';
			if (priceData[dataIndex].time > 0) {
				const date = new Date(priceData[dataIndex].time * 1000);
				timeLabel = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
			} else {
				timeLabel = `${dataIndex + 1}`;
			}
			
			ctx.fillText(timeLabel, x, height - 5);
		}

		// Legend
		ctx.fillStyle = '#888';
		ctx.font = '12px sans-serif';
		ctx.textAlign = 'center';
		
		if (signals.length > 0) {
			const buyCount = signals.filter(s => s.signal_type === 'buy').length;
			const sellCount = signals.filter(s => s.signal_type === 'sell').length;
			ctx.fillText(`📈 ${buyCount} Buy | ${sellCount} Sell | ${priceData.length} Candles`, width / 2, height - 20);
		} else {
			ctx.fillText(`${priceData.length} Candles (No signals generated)`, width / 2, height - 20);
		}
	}
</script>

<div class="signal-chart" bind:this={containerEl}>
	{#if klines.length === 0 && signals.length === 0}
		<div class="empty-state">
			<p>No data to display. Start a simulation to see price movements.</p>
		</div>
	{:else}
		<canvas 
			bind:this={canvasEl}
			style="width: 100%; height: {height}px;"
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
		width: 100%;
	}
</style>

<script lang="ts">
	interface Props {
		initialBalance?: number;
		currentBalance?: number;
		position?: number;
		positionToken?: string;
		entryPrice?: number;
		currentPrice?: number;
	}

	let { 
		initialBalance = 10000, 
		currentBalance = 10000, 
		position = 0,
		positionToken = '',
		entryPrice = 0,
		currentPrice = 0
	}: Props = $props();

	// Calculate metrics
	let positionValue = $derived(position * currentPrice);
	let totalValue = $derived(currentBalance + positionValue);
	let pnl = $derived(totalValue - initialBalance);
	let pnlPercent = $derived((pnl / initialBalance) * 100);
	let unrealizedPnL = $derived(position > 0 && entryPrice > 0 ? (currentPrice - entryPrice) / entryPrice * 100 : 0);
</script>

<div class="portfolio-summary">
	<div class="metric">
		<span class="label">Cash Balance</span>
		<span class="value">${currentBalance.toFixed(2)}</span>
	</div>
	
	{#if position > 0}
		<div class="metric">
			<span class="label">Position ({positionToken || 'Token'})</span>
			<span class="value highlight">{position.toFixed(6)}</span>
		</div>
		
		<div class="metric">
			<span class="label">Position Value</span>
			<span class="value">${positionValue.toFixed(2)}</span>
		</div>
		
		<div class="metric">
			<span class="label">Entry Price</span>
			<span class="value">${entryPrice.toFixed(8)}</span>
		</div>
		
		<div class="metric">
			<span class="label">Current Price</span>
			<span class="value">${currentPrice.toFixed(8)}</span>
		</div>
		
		<div class="metric">
			<span class="label">Unrealized P&L</span>
			<span class="value" class:positive={unrealizedPnL > 0} class:negative={unrealizedPnL < 0}>
				{unrealizedPnL >= 0 ? '+' : ''}{unrealizedPnL.toFixed(2)}%
			</span>
		</div>
	{/if}
	
	<div class="divider"></div>
	
	<div class="metric total">
		<span class="label">Total Value</span>
		<span class="value">${totalValue.toFixed(2)}</span>
	</div>
	
	<div class="metric">
		<span class="label">P&L</span>
		<span class="value large" class:positive={pnl > 0} class:negative={pnl < 0}>
			{pnl >= 0 ? '+' : ''}${pnl.toFixed(2)} ({pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
		</span>
	</div>
</div>

<style>
	.portfolio-summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 1rem;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.metric .label {
		font-size: 0.75rem;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.metric .value {
		font-size: 1rem;
		font-weight: 600;
		color: #fff;
		font-family: monospace;
	}

	.metric .value.highlight {
		color: #fbbf24;
	}

	.metric .value.large {
		font-size: 1.25rem;
	}

	.metric.total {
		grid-column: 1 / -1;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
	}

	.metric.total .value {
		font-size: 1.5rem;
		color: #667eea;
	}

	.positive {
		color: #22c55e !important;
	}

	.negative {
		color: #ef4444 !important;
	}

	.divider {
		display: none;
	}
</style>

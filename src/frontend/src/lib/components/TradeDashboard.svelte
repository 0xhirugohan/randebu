<script lang="ts">
	import type { TradeLogEntry } from '$lib/stores/simulationStore';

	interface Props {
		tradeLog: TradeLogEntry[];
	}

	let { tradeLog }: Props = $props();

	function formatTime(timestamp: number): string {
		const date = new Date(timestamp * 1000);
		return date.toLocaleString();
	}

	function getActionColor(action: string): string {
		switch (action) {
			case 'buy': return '#22c55e';
			case 'sell': return '#ef4444';
			default: return '#666';
		}
	}

	function getActionIcon(action: string): string {
		switch (action) {
			case 'buy': return '📈';
			case 'sell': return '📉';
			default: return '➡️';
		}
	}

	// Filter to show only buy/sell actions
	let tradeActions = $derived(tradeLog.filter(t => t.action !== 'hold'));
</script>

<div class="trade-dashboard">
	<div class="dashboard-header">
		<h3>Trade Activity</h3>
		<span class="trade-count">
			{tradeActions.length} trades
		</span>
	</div>

	{#if tradeActions.length === 0}
		<div class="empty-state">
			<p>No trades executed yet. Check the strategy configuration.</p>
		</div>
	{:else}
		<div class="trade-list">
			{#each tradeActions as entry}
				<div class="trade-entry action-{entry.action}">
					<div class="trade-time">
						<span class="action-icon">{getActionIcon(entry.action)}</span>
						<span class="action-badge" style="background: {getActionColor(entry.action)}">
							{entry.action.toUpperCase()}
						</span>
						<span class="time">{formatTime(entry.time)}</span>
					</div>
					<div class="trade-details">
						<div class="price">
							<span class="label">Price:</span>
							<span class="value">${entry.price.toFixed(8)}</span>
						</div>
						<div class="reason">
							<span class="label">Reason:</span>
							<span class="value">{entry.reason}</span>
						</div>
						{#if entry.action === 'sell' && entry.position > 0}
							<div class="pnl">
								<span class="label">Position:</span>
								<span class="value">{entry.position.toFixed(6)}</span>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.trade-dashboard {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		overflow: hidden;
	}

	.dashboard-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.02);
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.dashboard-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #fff;
	}

	.trade-count {
		font-size: 0.85rem;
		color: #888;
	}

	.empty-state {
		padding: 2rem;
		text-align: center;
		color: #666;
	}

	.trade-list {
		max-height: 300px;
		overflow-y: auto;
	}

	.trade-entry {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
		transition: background 0.2s;
	}

	.trade-entry:hover {
		background: rgba(255, 255, 255, 0.02);
	}

	.trade-entry.action-buy {
		border-left: 3px solid #22c55e;
	}

	.trade-entry.action-sell {
		border-left: 3px solid #ef4444;
	}

	.trade-time {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.action-icon {
		font-size: 1rem;
	}

	.action-badge {
		padding: 0.125rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: bold;
		color: #fff;
	}

	.time {
		font-size: 0.85rem;
		color: #888;
	}

	.trade-details {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.5rem;
		font-size: 0.85rem;
	}

	.trade-details .label {
		color: #666;
	}

	.trade-details .value {
		color: #fff;
		font-family: monospace;
	}

	.pnl .value {
		color: #fbbf24;
	}
</style>

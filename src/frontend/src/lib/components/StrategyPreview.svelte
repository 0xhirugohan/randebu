<script lang="ts">
	import type { StrategyConfig } from '$lib/api';

	interface Props {
		config: StrategyConfig | null;
		editable?: boolean;
		onUpdate?: (config: StrategyConfig) => void;
	}

	let { config, editable = false, onUpdate }: Props = $props();

	function getConditionDescription(condition: StrategyConfig['conditions'][0]): string {
		const timeframe = condition.timeframe ? ` within ${condition.timeframe}` : '';
		switch (condition.type) {
			case 'price_drop':
				return `${condition.token} drops by ${condition.threshold}%${timeframe}`;
			case 'price_rise':
				return `${condition.token} rises by ${condition.threshold}%${timeframe}`;
			case 'volume_spike':
				return `${condition.token} volume spikes by ${condition.threshold}%${timeframe}`;
			case 'price_level':
				return `${condition.token} crosses ${condition.direction} $${condition.price}`;
			default:
				return 'Unknown condition';
		}
	}

	function getActionDescription(action: StrategyConfig['actions'][0]): string {
		switch (action.type) {
			case 'buy':
				return `Buy ${action.amount_percent}% of ${action.token || 'portfolio'}`;
			case 'sell':
				return `Sell ${action.amount_percent}% of ${action.token || 'portfolio'}`;
			case 'hold':
				return 'Hold';
			default:
				return 'Unknown action';
		}
	}
</script>

<div class="strategy-preview">
	{#if !config || (config.conditions.length === 0 && config.actions.length === 0)}
		<div class="empty-state">
			<p>No strategy configured yet.</p>
			<p class="hint">Describe your trading strategy in the chat to create one.</p>
		</div>
	{:else}
		<div class="strategy-section">
			<h4>Conditions</h4>
			{#if config.conditions.length === 0}
				<p class="empty">No conditions set</p>
			{:else}
				<ul class="items-list">
					{#each config.conditions as condition, i}
						<li>
							<span class="condition-badge">{condition.type.replace('_', ' ')}</span>
							{getConditionDescription(condition)}
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		<div class="strategy-section">
			<h4>Actions</h4>
			{#if config.actions.length === 0}
				<p class="empty">No actions set</p>
			{:else}
				<ul class="items-list">
					{#each config.actions as action}
						<li>
							<span class="action-badge action-{action.type}">{action.type}</span>
							{getActionDescription(action)}
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		{#if config.risk_management}
			<div class="strategy-section">
				<h4>Risk Management</h4>
				<div class="risk-items">
					{#if config.risk_management.stop_loss_percent}
						<div class="risk-item">
							<span class="risk-label">Stop Loss</span>
							<span class="risk-value negative">{config.risk_management.stop_loss_percent}%</span>
						</div>
					{/if}
					{#if config.risk_management.take_profit_percent}
						<div class="risk-item">
							<span class="risk-label">Take Profit</span>
							<span class="risk-value positive">{config.risk_management.take_profit_percent}%</span>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.strategy-preview {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
	}

	.empty-state {
		text-align: center;
		padding: 1rem;
		color: #888;
	}

	.empty-state .hint {
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.5rem;
	}

	.strategy-section {
		margin-bottom: 1rem;
	}

	.strategy-section:last-child {
		margin-bottom: 0;
	}

	h4 {
		font-size: 0.85rem;
		font-weight: 600;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 0.75rem;
	}

	.items-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.items-list li {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.5rem 0;
		font-size: 0.9rem;
		color: #ccc;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.items-list li:last-child {
		border-bottom: none;
	}

	.condition-badge,
	.action-badge {
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.condition-badge {
		background: rgba(102, 126, 234, 0.2);
		color: #667eea;
	}

	.action-badge {
		min-width: 50px;
		text-align: center;
	}

	.action-buy {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}

	.action-sell {
		background: rgba(239, 68, 68, 0.2);
		color: #ef4444;
	}

	.action-hold {
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
	}

	.empty {
		color: #666;
		font-size: 0.9rem;
		font-style: italic;
	}

	.risk-items {
		display: flex;
		gap: 1.5rem;
	}

	.risk-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.risk-label {
		font-size: 0.75rem;
		color: #888;
	}

	.risk-value {
		font-size: 1.1rem;
		font-weight: 600;
	}

	.positive {
		color: #22c55e;
	}

	.negative {
		color: #ef4444;
	}
</style>
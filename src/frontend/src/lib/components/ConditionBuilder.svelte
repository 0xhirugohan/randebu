<script lang="ts">
	import type { Condition } from '$lib/api';
	import TokenPicker from './TokenPicker.svelte';

	interface Props {
		conditions: Condition[];
		onUpdate: (conditions: Condition[]) => void;
		disabled?: boolean;
	}

	let { conditions, onUpdate, disabled = false }: Props = $props();

	type ConditionType = Condition['type'];

	const conditionTypes: { value: ConditionType; label: string; description: string }[] = [
		{ value: 'price_drop', label: 'Price Drop', description: 'Trigger when price falls by X%' },
		{ value: 'price_rise', label: 'Price Rise', description: 'Trigger when price rises by X%' },
		{ value: 'volume_spike', label: 'Volume Spike', description: 'Trigger when volume increases by X%' },
		{ value: 'price_level', label: 'Price Level', description: 'Trigger when price crosses a level' },
	];

	const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];

	function addCondition() {
		const newCondition: Condition = {
			type: 'price_drop',
			token: '',
			threshold: 5,
			timeframe: '1h'
		};
		onUpdate([...conditions, newCondition]);
	}

	function removeCondition(index: number) {
		onUpdate(conditions.filter((_, i) => i !== index));
	}

	function updateCondition(index: number, updates: Partial<Condition>) {
		const updated = conditions.map((c, i) => 
			i === index ? { ...c, ...updates } : c
		);
		onUpdate(updated);
	}

	function getConditionDescription(condition: Condition): string {
		switch (condition.type) {
			case 'price_drop':
				return `Price drops ${condition.threshold || 0}% within ${condition.timeframe || '1h'}`;
			case 'price_rise':
				return `Price rises ${condition.threshold || 0}% within ${condition.timeframe || '1h'}`;
			case 'volume_spike':
				return `Volume spikes ${condition.threshold || 0}% within ${condition.timeframe || '1h'}`;
			case 'price_level':
				return `Price crosses ${condition.direction || 'above'} $${condition.price || 0}`;
			default:
				return 'Unknown condition';
		}
	}
</script>

<div class="condition-builder">
	<div class="conditions-header">
		<h4>Conditions</h4>
		<button type="button" class="add-btn" onclick={addCondition} {disabled}>
			+ Add Condition
		</button>
	</div>

	{#if conditions.length === 0}
		<div class="empty-state">
			<p>No conditions set</p>
			<p class="hint">Add a condition to define when your strategy triggers</p>
		</div>
	{:else}
		<div class="conditions-list">
			{#each conditions as condition, index}
				<div class="condition-card">
					<div class="condition-header">
						<span class="condition-number">#{index + 1}</span>
						<button 
							type="button" 
							class="remove-btn" 
							onclick={() => removeCondition(index)}
							disabled={disabled}
							aria-label="Remove condition"
						>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<line x1="18" y1="6" x2="6" y2="18"></line>
								<line x1="6" y1="6" x2="18" y2="18"></line>
							</svg>
						</button>
					</div>

					<div class="condition-fields">
						<div class="field">
							<label for="type-{index}">Type</label>
							<select
								id="type-{index}"
								value={condition.type}
								onchange={(e) => updateCondition(index, { type: (e.target as HTMLSelectElement).value as ConditionType })}
								disabled={disabled}
							>
								{#each conditionTypes as ct}
									<option value={ct.value}>{ct.label}</option>
								{/each}
							</select>
						</div>

						<TokenPicker
							label="Token"
							selectedToken={condition.token}
							selectedChain={condition.chain || ''}
							onSelect={(token, chain) => updateCondition(index, { token, chain })}
							disabled={disabled}
						/>

						{#if condition.type === 'price_level'}
							<div class="field">
								<label for="direction-{index}">Direction</label>
								<select
									id="direction-{index}"
									value={condition.direction || 'above'}
									onchange={(e) => updateCondition(index, { direction: (e.target as HTMLSelectElement).value as 'above' | 'below' })}
									disabled={disabled}
								>
									<option value="above">Above</option>
									<option value="below">Below</option>
								</select>
							</div>
							<div class="field">
								<label for="price-{index}">Price ($)</label>
								<input
									id="price-{index}"
									type="number"
									value={condition.price || ''}
									oninput={(e) => updateCondition(index, { price: parseFloat((e.target as HTMLInputElement).value) || undefined })}
									placeholder="0.000001"
									step="any"
									min="0"
									disabled={disabled}
								/>
							</div>
						{:else}
							<div class="field">
								<label for="threshold-{index}">Threshold (%)</label>
								<input
									id="threshold-{index}"
									type="number"
									value={condition.threshold || ''}
									oninput={(e) => updateCondition(index, { threshold: parseFloat((e.target as HTMLInputElement).value) || undefined })}
									placeholder="5"
									step="any"
									min="0"
									disabled={disabled}
								/>
							</div>
							<div class="field">
								<label for="timeframe-{index}">Timeframe</label>
								<select
									id="timeframe-{index}"
									value={condition.timeframe || '1h'}
									onchange={(e) => updateCondition(index, { timeframe: (e.target as HTMLSelectElement).value })}
									disabled={disabled}
								>
									{#each timeframes as tf}
										<option value={tf}>{tf}</option>
									{/each}
								</select>
							</div>
						{/if}
					</div>

					<div class="condition-preview">
						<span class="preview-label">Summary:</span>
						{getConditionDescription(condition)}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.condition-builder {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1rem;
	}

	.conditions-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	h4 {
		margin: 0;
		font-size: 0.9rem;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.add-btn {
		padding: 0.5rem 1rem;
		background: rgba(102, 126, 234, 0.2);
		color: #667eea;
		border: 1px solid rgba(102, 126, 234, 0.4);
		border-radius: 6px;
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}

	.add-btn:hover:not(:disabled) {
		background: rgba(102, 126, 234, 0.3);
	}

	.add-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.empty-state {
		text-align: center;
		padding: 1.5rem;
		color: #666;
	}

	.empty-state .hint {
		font-size: 0.85rem;
		margin-top: 0.5rem;
	}

	.conditions-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.condition-card {
		background: rgba(0, 0, 0, 0.2);
		border: 1px solid rgba(255, 255, 255, 0.05);
		border-radius: 8px;
		padding: 1rem;
	}

	.condition-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.condition-number {
		font-size: 0.85rem;
		font-weight: 600;
		color: #667eea;
	}

	.remove-btn {
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 4px;
		transition: background 0.2s, color 0.2s;
	}

	.remove-btn:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.2);
		color: #ef4444;
	}

	.remove-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.condition-fields {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.field label {
		font-size: 0.8rem;
		color: #888;
	}

	input,
	select {
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.15);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 0.9rem;
	}

	input:focus,
	select:focus {
		outline: none;
		border-color: #667eea;
	}

	input:disabled,
	select:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	input[type="number"] {
		-moz-appearance: textfield;
	}

	input[type="number"]::-webkit-inner-spin-button,
	input[type="number"]::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.condition-preview {
		padding-top: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.05);
		font-size: 0.85rem;
		color: #aaa;
	}

	.preview-label {
		color: #666;
		margin-right: 0.5rem;
	}
</style>
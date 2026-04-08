<script lang="ts">
	import type { Bot } from '$lib/api';

	interface Props {
		bots: Bot[];
		selectedBotId?: string | null;
		onSelect: (botId: string) => void;
		disabled?: boolean;
		label?: string;
	}

	let { bots, selectedBotId = null, onSelect, disabled = false, label = 'Select Bot' }: Props = $props();

	function handleChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		onSelect(target.value);
	}

	const MAX_BOTS = 3;
</script>

<div class="bot-selector">
	{#if label}
		<label for="bot-select">{label}</label>
	{/if}
	<div class="select-wrapper">
		<select
			id="bot-select"
			onchange={handleChange}
			disabled={disabled || bots.length === 0}
			value={selectedBotId || ''}
		>
			{#if bots.length === 0}
				<option value="" disabled>No bots available</option>
			{:else}
				{#each bots as bot}
					<option value={bot.id}>{bot.name}</option>
				{/each}
			{/if}
		</select>
		<span class="bot-count">{bots.length}/{MAX_BOTS}</span>
	</div>
</div>

<style>
	.bot-selector {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-size: 0.9rem;
		color: #888;
	}

	.select-wrapper {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	select {
		flex: 1;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		cursor: pointer;
		appearance: none;
		background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23888' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
		background-repeat: no-repeat;
		background-position: right 1rem center;
		padding-right: 2.5rem;
	}

	select:focus {
		outline: none;
		border-color: #667eea;
	}

	select:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.bot-count {
		font-size: 0.8rem;
		color: #666;
		white-space: nowrap;
	}
</style>
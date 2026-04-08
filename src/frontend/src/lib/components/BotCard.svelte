<script lang="ts">
	import type { Bot } from '$lib/api';

	interface Props {
		bot: Bot;
		onOpen?: (botId: string) => void;
		onDelete?: (botId: string) => void;
		showActions?: boolean;
	}

	let { bot, onOpen, onDelete, showActions = true }: Props = $props();

	function handleOpen() {
		onOpen?.(bot.id);
	}

	function handleDelete(e: Event) {
		e.stopPropagation();
		onDelete?.(bot.id);
	}
</script>

<div class="bot-card" onclick={handleOpen} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && handleOpen()}>
	<div class="bot-info">
		<h3>{bot.name}</h3>
		{#if bot.description}
			<p class="bot-description">{bot.description}</p>
		{/if}
		<span class="bot-status status-{bot.status}">{bot.status}</span>
	</div>
	{#if showActions}
		<div class="bot-actions" onclick={(e) => e.stopPropagation()} role="group">
			<button class="btn btn-primary" onclick={handleOpen}>Open</button>
			<button class="btn btn-danger" onclick={handleDelete}>Delete</button>
		</div>
	{/if}
</div>

<style>
	.bot-card {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
		cursor: pointer;
		transition: transform 0.2s, border-color 0.2s;
	}

	.bot-card:hover {
		transform: translateY(-2px);
		border-color: rgba(255, 255, 255, 0.2);
	}

	.bot-card:focus {
		outline: 2px solid #667eea;
		outline-offset: 2px;
	}

	.bot-info {
		margin-bottom: 1rem;
	}

	.bot-info h3 {
		margin: 0 0 0.5rem;
		font-size: 1.25rem;
	}

	.bot-description {
		color: #888;
		font-size: 0.9rem;
		margin: 0 0 0.75rem;
	}

	.bot-status {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.status-draft {
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
	}

	.status-active {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}

	.status-paused {
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
	}

	.bot-actions {
		display: flex;
		gap: 0.75rem;
	}

	.btn {
		padding: 0.5rem 1rem;
		border-radius: 8px;
		font-weight: 500;
		font-size: 0.9rem;
		cursor: pointer;
		border: none;
		transition: transform 0.2s, opacity 0.2s;
	}

	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.btn-danger {
		background: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
		border: 1px solid rgba(239, 68, 68, 0.4);
	}

	.btn:hover {
		transform: translateY(-2px);
	}
</style>
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, botsStore, setBots, addBot, removeBot, userStore, logout } from '$lib/stores';
	import { api } from '$lib/api';
	import { BotCard } from '$lib/components';

	let showCreateModal = $state(false);
	let newBotName = $state('');
	let newBotDescription = $state('');
	let isCreating = $state(false);
	let createError = $state('');

	onMount(async () => {
		if (!$isAuthenticated && !$isLoading) {
			goto('/login');
			return;
		}
		if ($isAuthenticated) {
			await loadBots();
		}
	});

	async function loadBots() {
		try {
			const bots = await api.bots.list();
			setBots(bots);
		} catch (e) {
			console.error('Failed to load bots:', e);
		}
	}

	async function createBot() {
		if (!newBotName.trim()) return;
		createError = '';
		isCreating = true;
		try {
			const bot = await api.bots.create(newBotName, newBotDescription);
			addBot(bot);
			showCreateModal = false;
			newBotName = '';
			newBotDescription = '';
			goto(`/bot/${bot.id}`);
		} catch (e) {
			createError = e instanceof Error ? e.message : 'Failed to create bot';
		} finally {
			isCreating = false;
		}
	}

	async function deleteBot(botId: string) {
		if (!confirm('Are you sure you want to delete this bot?')) return;
		try {
			await api.bots.delete(botId);
			removeBot(botId);
		} catch (e) {
			console.error('Failed to delete bot:', e);
		}
	}

	function handleLogout() {
		logout();
		goto('/');
	}
</script>

<svelte:head>
	<title>Dashboard - Randebu</title>
</svelte:head>

<main>
	<header>
		<h1>Dashboard</h1>
		<div class="header-actions">
			<span class="user-email">{$userStore?.email}</span>
			<a href="/settings" class="btn btn-secondary">Settings</a>
			<button onclick={handleLogout} class="btn btn-secondary">Logout</button>
		</div>
	</header>

	<section class="bots-section">
		<div class="section-header">
			<h2>Your Bots ({$botsStore.length}/3)</h2>
			{#if $botsStore.length < 3}
				<button onclick={() => showCreateModal = true} class="btn btn-primary">
					Create New Bot
				</button>
			{/if}
		</div>

		{#if $botsStore.length === 0}
			<div class="empty-state">
				<p>You haven't created any bots yet.</p>
				<p>Create your first bot to start trading!</p>
			</div>
		{:else}
			<div class="bots-grid">
				{#each $botsStore as bot}
					<BotCard {bot} onOpen={(id) => goto(`/bot/${id}`)} onDelete={deleteBot} />
				{/each}
			</div>
		{/if}
	</section>

	{#if showCreateModal}
		<div class="modal-overlay" onclick={() => showCreateModal = false}>
			<div class="modal" onclick={(e) => e.stopPropagation()}>
				<h2>Create New Bot</h2>
				{#if createError}
					<div class="error">{createError}</div>
				{/if}
				<form onsubmit={(e) => { e.preventDefault(); createBot(); }}>
					<div class="field">
						<label for="botName">Bot Name</label>
						<input type="text" id="botName" bind:value={newBotName} required />
					</div>
					<div class="field">
						<label for="botDescription">Description (optional)</label>
						<textarea id="botDescription" bind:value={newBotDescription} rows="3"></textarea>
					</div>
					<div class="modal-actions">
						<button type="button" onclick={() => showCreateModal = false} class="btn btn-secondary">
							Cancel
						</button>
						<button type="submit" disabled={isCreating}>
							{isCreating ? 'Creating...' : 'Create'}
						</button>
					</div>
				</form>
			</div>
		</div>
	{/if}
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: #0f0f0f;
		color: #fff;
	}

	main {
		min-height: 100vh;
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	h1 {
		margin: 0;
		font-size: 2rem;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.user-email {
		color: #888;
		font-size: 0.9rem;
	}

	h2 {
		margin: 0;
		font-size: 1.25rem;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.bots-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.btn {
		padding: 0.5rem 1rem;
		border-radius: 8px;
		text-decoration: none;
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

	.btn-secondary {
		background: rgba(255, 255, 255, 0.1);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.btn:hover {
		transform: translateY(-2px);
	}

	.empty-state {
		text-align: center;
		padding: 3rem;
		color: #888;
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
	}

	.modal {
		background: #1a1a1a;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 2rem;
		width: 100%;
		max-width: 450px;
	}

	.modal h2 {
		margin: 0 0 1.5rem;
	}

	.error {
		background: rgba(239, 68, 68, 0.2);
		border: 1px solid #ef4444;
		color: #fca5a5;
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.field {
		margin-bottom: 1rem;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		color: #ccc;
		font-size: 0.9rem;
	}

	input, textarea {
		width: 100%;
		padding: 0.75rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		box-sizing: border-box;
	}

	input:focus, textarea:focus {
		outline: none;
		border-color: #667eea;
	}

	.modal-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		margin-top: 1.5rem;
	}
</style>

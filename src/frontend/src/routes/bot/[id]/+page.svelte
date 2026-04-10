<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, chatStore, addMessage, setMessages, clearChat, currentBotStore, setCurrentBot } from '$lib/stores';
	import { api } from '$lib/api';
	import { ChatInterface, StrategyPreview, ProUpgradeBanner } from '$lib/components';

	let botId = $derived($page.params.id);
	let isSending = $state(false);
	let showStrategy = $state(false);

	onMount(async () => {
		if (!$isAuthenticated && !$isLoading) {
			goto('/login');
			return;
		}
		if ($isAuthenticated && botId) {
			await loadBot();
			await loadChatHistory();
		}
	});

	async function loadBot() {
		try {
			const bot = await api.bots.get(botId);
			setCurrentBot(bot);
		} catch (e) {
			goto('/dashboard');
		}
	}

	async function loadChatHistory() {
		try {
			const history = await api.bots.getHistory(botId);
			setMessages(history);
		} catch (e) {
			console.error('Failed to load chat history:', e);
		}
	}

	async function handleSendMessage(message: string) {
		if (isSending) return;
		
		isSending = true;

		// Add user's message immediately
		addMessage({ role: 'user', content: message });

		try {
			const response = await api.bots.chat(botId, message);
			addMessage({ role: 'assistant', content: response.response });
			
			if (response.strategy_config) {
				const bot = await api.bots.get(botId);
				setCurrentBot(bot);
			}
		} catch (e) {
			addMessage({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' });
		} finally {
			isSending = false;
		}
	}

	function toggleStrategy() {
		showStrategy = !showStrategy;
	}
</script>

<svelte:head>
	<title>{$currentBotStore?.name || 'Bot'} - Randebu</title>
</svelte:head>

<main>
	<header>
		<div class="header-left">
			<a href="/dashboard" class="back-link">← Dashboard</a>
			<h1>{$currentBotStore?.name || 'Loading...'}</h1>
		</div>
		<div class="header-actions">
			{#if $currentBotStore?.strategy_config}
				<button class="btn btn-secondary" onclick={toggleStrategy}>
					{showStrategy ? 'Hide' : 'Show'} Strategy
				</button>
			{/if}
			<a href="/bot/{botId}/backtest" class="btn btn-secondary">Backtest</a>
			<a href="/bot/{botId}/simulate" class="btn btn-secondary">Simulate</a>
		</div>
	</header>

	{#if showStrategy && $currentBotStore?.strategy_config}
		<div class="strategy-panel">
			<StrategyPreview config={$currentBotStore.strategy_config} />
		</div>
	{/if}

	<div class="chat-wrapper">
		<ChatInterface
			bot={$currentBotStore}
			messages={$chatStore}
			{isSending}
			onSendMessage={handleSendMessage}
		/>
	</div>

	<ProUpgradeBanner feature="Auto-execute trades with your bot" />
</main>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: #0f0f0f;
		color: #fff;
	}

	main {
		height: 100vh;
		display: flex;
		flex-direction: column;
		max-width: 900px;
		margin: 0 auto;
		padding: 1rem;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 1rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
		margin-bottom: 1rem;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.back-link {
		color: #667eea;
		text-decoration: none;
		font-size: 0.9rem;
	}

	.back-link:hover {
		text-decoration: underline;
	}

	h1 {
		margin: 0;
		font-size: 1.5rem;
	}

	.header-actions {
		display: flex;
		gap: 0.75rem;
	}

	.btn {
		padding: 0.5rem 1rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 500;
		font-size: 0.9rem;
		cursor: pointer;
		border: none;
		transition: transform 0.2s;
	}

	.btn-secondary {
		background: rgba(255, 255, 255, 0.1);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.btn:hover {
		transform: translateY(-2px);
	}

	.strategy-panel {
		margin-bottom: 1rem;
	}

	.chat-wrapper {
		flex: 1;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
</style>
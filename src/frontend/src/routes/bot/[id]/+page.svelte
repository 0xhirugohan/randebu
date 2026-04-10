<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, chatStore, addMessage, setMessages, clearChat, currentBotStore, setCurrentBot } from '$lib/stores';
	import { api } from '$lib/api';
	import { ChatInterface, StrategyPreview } from '$lib/components';
	import type { TokenSearchResult } from '$lib/api';

	let botId = $derived($page.params.id);
	let isSending = $state(false);
	let showStrategy = $state(false);
	
	// Token address confirmation modal state
	let showTokenConfirm = $state(false);
	let pendingStrategyData = $state<any>(null);
	let tokenAddressInput = $state('');
	let confirmingMessage = $state('');
	let tokenSearchResults = $state<TokenSearchResult[]>([]);

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

		// Add user's message immediately so it shows even before API response
		addMessage({ role: 'user', content: message });

		try {
			// Add timeout to prevent hanging requests
			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 30000);
			
			const response = await api.bots.chat(botId, message, controller.signal);
			clearTimeout(timeoutId);
			
			// Check if token address confirmation is needed
			if (response.strategy_needs_confirmation && response.strategy_data) {
				// Show token confirmation modal
				pendingStrategyData = response.strategy_data;
				confirmingMessage = response.response;
				tokenAddressInput = '';
				tokenSearchResults = response.token_search_results || [];
				showTokenConfirm = true;
			}
			
			// Add assistant response with thinking
			addMessage({ role: 'assistant', content: response.response, thinking: response.thinking || null });
			
			if (response.strategy_config) {
				const bot = await api.bots.get(botId);
				setCurrentBot(bot);
			}
		} catch (e) {
			if (e instanceof Error && e.name === 'AbortError') {
				addMessage({ role: 'assistant', content: 'Request timed out. Please try again.', thinking: null });
			} else {
				addMessage({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', thinking: null });
			}
		} finally {
			isSending = false;
		}
	}

	function toggleStrategy() {
		showStrategy = !showStrategy;
	}
	
	async function confirmTokenAddress() {
		if (!tokenAddressInput.trim() || !pendingStrategyData) {
			showTokenConfirm = false;
			return;
		}
		
		// Update the pending strategy with the token address
		const updatedStrategy = { ...pendingStrategyData };
		
		// Update conditions with token address
		if (updatedStrategy.conditions) {
			updatedStrategy.conditions = updatedStrategy.conditions.map((cond: any) => ({
				...cond,
				token_address: tokenAddressInput.trim()
			}));
		}
		
		// Update actions with token address
		if (updatedStrategy.actions) {
			updatedStrategy.actions = updatedStrategy.actions.map((action: any) => ({
				...action,
				token_address: tokenAddressInput.trim()
			}));
		}
		
		try {
			// Update bot with the strategy
			await api.bots.update(botId, { strategy_config: updatedStrategy });
			
			// Refresh bot data
			const bot = await api.bots.get(botId);
			setCurrentBot(bot);
			
			// Add success message
			addMessage({ role: 'assistant', content: `Perfect! I've saved your strategy with the token address. You can now run backtests!`, thinking: null });
		} catch (e) {
			addMessage({ role: 'assistant', content: 'Failed to save strategy. Please try again.', thinking: null });
		}
		
		showTokenConfirm = false;
		pendingStrategyData = null;
		tokenAddressInput = '';
		tokenSearchResults = [];
	}
	
	function selectTokenResult(result: TokenSearchResult) {
		tokenAddressInput = result.address;
	}
	
	function cancelTokenConfirm() {
		showTokenConfirm = false;
		pendingStrategyData = null;
		tokenAddressInput = '';
		tokenSearchResults = [];
	}
</script>

<svelte:head>
	<title>{$currentBotStore?.name || 'Bot'} - Randebu</title>
</svelte:head>

<main>
	{#if showTokenConfirm}
		<div class="modal-overlay" onclick={cancelTokenConfirm}>
			<div class="modal-content" onclick={(e) => e.stopPropagation()}>
				<h3>Select Token Address</h3>
				<p class="modal-message">{confirmingMessage}</p>
				
				{#if tokenSearchResults.length > 0}
					<div class="token-results">
						<p class="modal-hint">Select a token:</p>
						{#each tokenSearchResults as result}
							<button class="token-result" onclick={() => selectTokenResult(result)}>
								<span class="token-symbol">{result.symbol}</span>
								<span class="token-name">{result.name}</span>
								<span class="token-address">{result.address.slice(0, 10)}...{result.address.slice(-8)}</span>
							</button>
						{/each}
					</div>
					<p class="modal-divider">or enter manually:</p>
				{/if}
				
				<input type="text" class="token-input" bind:value={tokenAddressInput} placeholder="0x..."/>
				<div class="modal-actions">
					<button class="btn btn-secondary" onclick={cancelTokenConfirm}>Cancel</button>
					<button class="btn btn-primary" onclick={confirmTokenAddress} disabled={!tokenAddressInput.trim()}>Confirm</button>
				</div>
			</div>
		</div>
	{/if}
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
			isSending={isSending}
			onSendMessage={handleSendMessage}
		/>
	</div>

	<!-- <ProUpgradeBanner feature="Auto-execute trades with your bot" /> -->
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

	/* Modal Styles */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: rgba(20, 20, 20, 0.95);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 1.5rem;
		max-width: 450px;
		width: 90%;
	}

	.modal-content h3 {
		margin: 0 0 1rem;
		color: #667eea;
	}

	.modal-message {
		color: #ccc;
		margin-bottom: 0.5rem;
		line-height: 1.5;
	}

	.modal-hint {
		color: #888;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.token-input {
		width: 100%;
		padding: 0.75rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		font-family: 'Monaco', 'Menlo', monospace;
		box-sizing: border-box;
	}

	.token-input:focus {
		outline: none;
		border-color: #667eea;
	}

	.modal-actions {
		display: flex;
		gap: 0.75rem;
		margin-top: 1rem;
		justify-content: flex-end;
	}

	.btn-primary {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
	}

	.btn-primary:hover:not(:disabled) {
		transform: translateY(-2px);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Token Results */
	.token-results {
		max-height: 200px;
		overflow-y: auto;
		margin-bottom: 1rem;
	}

	.token-result {
		width: 100%;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		margin-bottom: 0.5rem;
		cursor: pointer;
		text-align: left;
		color: #fff;
		transition: background 0.2s;
	}

	.token-result:hover {
		background: rgba(102, 126, 234, 0.2);
		border-color: rgba(102, 126, 234, 0.5);
	}

	.token-result:last-child {
		margin-bottom: 0;
	}

	.token-symbol {
		font-weight: 600;
		color: #667eea;
		min-width: 60px;
	}

	.token-name {
		flex: 1;
		color: #ccc;
		font-size: 0.9rem;
	}

	.token-address {
		font-size: 0.75rem;
		color: #666;
		font-family: 'Monaco', 'Menlo', monospace;
	}

	.modal-divider {
		text-align: center;
		color: #666;
		font-size: 0.85rem;
		margin: 1rem 0;
	}
</style>
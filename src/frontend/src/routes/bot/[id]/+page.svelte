<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, chatStore, addMessage, setMessages, clearChat, currentBotStore, setCurrentBot } from '$lib/stores';
	import { api } from '$lib/api';

	let botId = $derived($page.params.id);
	let messageInput = $state('');
	let isSending = $state(false);
	let chatContainer: HTMLDivElement;

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
			scrollToBottom();
		} catch (e) {
			console.error('Failed to load chat history:', e);
		}
	}

	async function sendMessage() {
		if (!messageInput.trim() || isSending) return;
		
		const userMessage = messageInput;
		messageInput = '';
		isSending = true;

		addMessage({ role: 'user', content: userMessage });
		scrollToBottom();

		try {
			const response = await api.bots.chat(botId, userMessage);
			addMessage({ role: 'assistant', content: response.response });
			
			if (response.strategy_config) {
				const bot = await api.bots.get(botId);
				setCurrentBot(bot);
			}
		} catch (e) {
			addMessage({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' });
		} finally {
			isSending = false;
			scrollToBottom();
		}
	}

	function scrollToBottom() {
		setTimeout(() => {
			if (chatContainer) {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}
		}, 50);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
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
			<a href="/bot/{botId}/backtest" class="btn btn-secondary">Backtest</a>
			<a href="/bot/{botId}/simulate" class="btn btn-secondary">Simulate</a>
		</div>
	</header>

	<div class="chat-container" bind:this={chatContainer}>
		{#if $chatStore.length === 0}
			<div class="welcome-message">
				<p>Welcome to {$currentBotStore?.name}! Describe your trading strategy in plain English.</p>
				<p class="hint">Example: "Buy PEPE when the price drops by 5% within 1 hour"</p>
			</div>
		{/if}

		{#each $chatStore as message}
			<div class="message {message.role}">
				<div class="message-content">
					{message.content}
				</div>
				<div class="message-time">
					{message.timestamp.toLocaleTimeString()}
				</div>
			</div>
		{/each}

		{#if isSending}
			<div class="message assistant">
				<div class="message-content typing">
					<span class="dot"></span>
					<span class="dot"></span>
					<span class="dot"></span>
				</div>
			</div>
		{/if}
	</div>

	{#if $currentBotStore}
		<div class="input-container">
			<textarea
				bind:value={messageInput}
				onkeydown={handleKeydown}
				placeholder="Describe your trading strategy..."
				rows="1"
				disabled={isSending}
			></textarea>
			<button onclick={sendMessage} disabled={isSending || !messageInput.trim()}>
				Send
			</button>
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

	.chat-container {
		flex: 1;
		overflow-y: auto;
		padding: 1rem 0;
	}

	.welcome-message {
		text-align: center;
		padding: 2rem;
		color: #888;
	}

	.welcome-message .hint {
		font-size: 0.85rem;
		margin-top: 1rem;
		color: #666;
	}

	.message {
		display: flex;
		flex-direction: column;
		margin-bottom: 1rem;
	}

	.message.user {
		align-items: flex-end;
	}

	.message.assistant {
		align-items: flex-start;
	}

	.message-content {
		max-width: 70%;
		padding: 0.75rem 1rem;
		border-radius: 12px;
		line-height: 1.5;
	}

	.message.user .message-content {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-bottom-right-radius: 4px;
	}

	.message.assistant .message-content {
		background: rgba(255, 255, 255, 0.1);
		border-bottom-left-radius: 4px;
	}

	.message-time {
		font-size: 0.7rem;
		color: #666;
		margin-top: 0.25rem;
		padding: 0 0.5rem;
	}

	.typing {
		display: flex;
		gap: 4px;
		padding: 1rem 1.25rem;
	}

	.dot {
		width: 8px;
		height: 8px;
		background: #888;
		border-radius: 50%;
		animation: typing 1.4s infinite;
	}

	.dot:nth-child(2) {
		animation-delay: 0.2s;
	}

	.dot:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes typing {
		0%, 60%, 100% {
			transform: translateY(0);
			opacity: 0.4;
		}
		30% {
			transform: translateY(-4px);
			opacity: 1;
		}
	}

	.input-container {
		display: flex;
		gap: 0.75rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	textarea {
		flex: 1;
		padding: 0.75rem 1rem;
		border-radius: 12px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		resize: none;
		font-family: inherit;
	}

	textarea:focus {
		outline: none;
		border-color: #667eea;
	}

	button {
		padding: 0.75rem 1.5rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: transform 0.2s;
	}

	button:hover:not(:disabled) {
		transform: translateY(-2px);
	}

	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>

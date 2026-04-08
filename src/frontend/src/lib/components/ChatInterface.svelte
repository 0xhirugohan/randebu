<script lang="ts">
	import type { Bot } from '$lib/api';
	import type { ChatMessage } from '$lib/stores/chatStore';

	interface Props {
		bot: Bot | null;
		messages: ChatMessage[];
		isSending?: boolean;
		onSendMessage: (message: string) => void;
		onSelectBot?: (botId: string) => void;
		availableBots?: Bot[];
		showBotSelector?: boolean;
	}

	let {
		bot,
		messages,
		isSending = false,
		onSendMessage,
		onSelectBot,
		availableBots = [],
		showBotSelector = false
	}: Props = $props();

	let messageInput = $state('');
	let chatContainer: HTMLDivElement;

	function handleSend() {
		if (!messageInput.trim()) return;
		onSendMessage(messageInput);
		messageInput = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleBotChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		if (onSelectBot && target.value) {
			onSelectBot(target.value);
		}
	}

	$effect(() => {
		if (messages.length && chatContainer) {
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 50);
		}
	});
</script>

<div class="chat-interface">
	{#if showBotSelector && availableBots.length > 0}
		<div class="bot-selector">
			<label for="bot-select">Active Bot:</label>
			<select id="bot-select" onchange={handleBotChange}>
				{#each availableBots as availableBot}
					<option value={availableBot.id} selected={availableBot.id === bot?.id}>
						{availableBot.name}
					</option>
				{/each}
			</select>
		</div>
	{/if}

	<div class="chat-messages" bind:this={chatContainer}>
		{#if messages.length === 0}
			<div class="welcome-message">
				<p>Welcome to {bot?.name || 'your bot'}! Describe your trading strategy in plain English.</p>
				<p class="hint">Example: "Buy PEPE when the price drops by 5% within 1 hour"</p>
			</div>
		{/if}

		{#each messages as message}
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

	{#if bot}
		<div class="input-container">
			<textarea
				bind:value={messageInput}
				onkeydown={handleKeydown}
				placeholder="Describe your trading strategy..."
				rows="1"
				disabled={isSending}
			></textarea>
			<button onclick={handleSend} disabled={isSending || !messageInput.trim()}>
				Send
			</button>
		</div>
	{/if}
</div>

<style>
	.chat-interface {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.bot-selector {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: rgba(255, 255, 255, 0.03);
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.bot-selector label {
		font-size: 0.9rem;
		color: #888;
	}

	.bot-selector select {
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 0.9rem;
		cursor: pointer;
	}

	.bot-selector select:focus {
		outline: none;
		border-color: #667eea;
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
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

	.message.system {
		align-items: center;
	}

	.message-content {
		max-width: 70%;
		padding: 0.75rem 1rem;
		border-radius: 12px;
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;
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

	.message.system .message-content {
		background: rgba(251, 191, 36, 0.1);
		color: #fbbf24;
		font-size: 0.9rem;
		border: 1px solid rgba(251, 191, 36, 0.3);
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
		padding: 1rem;
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
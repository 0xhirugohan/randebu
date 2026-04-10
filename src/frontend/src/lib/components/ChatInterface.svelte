<script lang="ts">
	import type { Bot } from '$lib/api';
	import type { ChatMessage } from '$lib/stores/chatStore';
	import { parseMarkdown } from '$lib/utils/markdown';

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
	let expandedThinking: Record<string, boolean> = $state({});

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

	function toggleThinkingExpand(messageId: string) {
		expandedThinking[messageId] = !expandedThinking[messageId];
	}

	$effect(() => {
		if (messages.length && chatContainer) {
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 50);
		}
	});

	function renderContent(content: string) {
		return parseMarkdown(content);
	}
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
				{#if message.role === 'assistant' && message.thinking}
					{@const firstLine = message.thinking.split('\n')[0]}
					{@const isExpanded = expandedThinking[message.id] ?? false}
					<div class="thinking-section">
						<button class="thinking-toggle" onclick={() => toggleThinkingExpand(message.id)}>
							<span class="thinking-icon">{isExpanded ? '▼' : '▶'}</span>
							<span class="thinking-label">{isExpanded ? 'Hide reasoning' : 'Show reasoning'}</span>
							{#if !isExpanded}
								<span class="thinking-preview"> — {firstLine.slice(0, 60)}{firstLine.length > 60 ? '...' : ''}</span>
							{/if}
						</button>
						{#if isExpanded}
							<div class="thinking-content">
								{message.thinking}
							</div>
						{/if}
					</div>
				{/if}
				<div class="message-content">
					{#each renderContent(message.content) as segment}
						{#if segment.type === 'bold'}
							<strong>{segment.content}</strong>
						{:else if segment.type === 'italic'}
							<em>{segment.content}</em>
						{:else if segment.type === 'code'}
							<code class="inline-code">{segment.content}</code>
						{:else if segment.type === 'codeBlock'}
							<pre class="code-block"><code>{segment.content}</code></pre>
						{:else if segment.type === 'link'}
							<a href={segment.content} target="_blank" rel="noopener noreferrer">{segment.content}</a>
						{:else if segment.type === 'list' && segment.items}
							<ul>
								{#each segment.items as item}
									<li>{item}</li>
								{/each}
							</ul>
						{:else if segment.type === 'table' && segment.headers && segment.rows}
							<div class="table-wrapper">
								<table class="markdown-table">
									<thead>
									<tr>
										{#each segment.headers as header}
											<th>{header}</th>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each segment.rows as row}
										<tr>
											{#each row as cell}
												<td>{cell}</td>
											{/each}
									</tr>
									{/each}
								</tbody>
							</table>
							</div>
						{:else if segment.type === 'heading'}
							<h4 class="content-heading">{segment.content}</h4>
						{:else if segment.type === 'lineBreak'}
							<br />
						{:else}
							{segment.content}
						{/if}
					{/each}
				</div>
				<div class="message-time">
					{message.timestamp.toLocaleTimeString()}
				</div>
			</div>
	{/each}

		{#if isSending}
			<div class="message assistant">
				<div class="message-content">
					<div class="typing">
						<span class="dot"></span>
						<span class="dot"></span>
						<span class="dot"></span>
					</div>
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
			></textarea>
			<button onclick={handleSend}>
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

	.thinking-section {
		margin-bottom: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: rgba(255, 255, 255, 0.03);
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.thinking-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.8rem;
		transition: background 0.2s;
		width: 100%;
		text-align: left;
	}

	.thinking-toggle:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.thinking-icon {
		font-size: 0.6rem;
		color: #667eea;
	}

	.thinking-label {
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #667eea;
	}

	.thinking-preview {
		color: #666;
		font-style: italic;
		font-weight: normal;
		text-transform: none;
		letter-spacing: normal;
	}

	.thinking-content {
		color: #888;
		font-size: 0.85rem;
		padding: 0.75rem 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		margin-top: 0.5rem;
		white-space: pre-wrap;
		line-height: 1.6;
	}

	.message.system .message-content {
		background: rgba(251, 191, 36, 0.1);
		color: #fbbf24;
		font-size: 0.9rem;
		border: 1px solid rgba(251, 191, 36, 0.3);
	}

	.message.thinking .message-content {
		background: rgba(255, 255, 255, 0.05);
		border: 1px dashed rgba(255, 255, 255, 0.2);
	}

	.message-time {
		font-size: 0.7rem;
		color: #666;
		margin-top: 0.25rem;
		padding: 0 0.5rem;
	}

	.thinking-header {
		display: flex;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.thinking-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.8rem;
		transition: background 0.2s;
	}

	.thinking-toggle:hover {
		background: rgba(255, 255, 255, 0.1);
	}

	.thinking-icon {
		font-size: 0.6rem;
	}

	.thinking-label {
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.thinking-content {
		color: #999;
		font-size: 0.9rem;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
		margin-top: 0.5rem;
	}

	.inline-code {
		background: rgba(0, 0, 0, 0.3);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.85em;
	}

	.code-block {
		background: rgba(0, 0, 0, 0.4);
		padding: 0.75rem;
		border-radius: 6px;
		overflow-x: auto;
		font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
		font-size: 0.85rem;
		margin: 0.5rem 0;
	}

	.code-block code {
		white-space: pre;
	}

	ul {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}

	li {
		margin: 0.25rem 0;
	}

	a {
		color: #667eea;
		text-decoration: none;
	}

	.content-heading {
		font-size: 1rem;
		font-weight: 600;
		margin: 1rem 0 0.5rem;
		color: #fff;
	}

	.content-heading:first-child {
		margin-top: 0;
	}

	.table-wrapper {
		overflow-x: auto;
		margin: 0.75rem 0;
	}

	.markdown-table {
		border-collapse: collapse;
		width: 100%;
		font-size: 0.85rem;
		background: rgba(0, 0, 0, 0.2);
		border-radius: 6px;
		overflow: hidden;
	}

	.markdown-table th,
	.markdown-table td {
		padding: 0.5rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.markdown-table th {
		background: rgba(102, 126, 234, 0.2);
		font-weight: 600;
		color: #667eea;
	}

	.markdown-table tr:last-child td {
		border-bottom: none;
	}

	.markdown-table tr:hover td {
		background: rgba(255, 255, 255, 0.05);
	}

	a:hover {
		text-decoration: underline;
	}

	.typing {
		display: flex;
		gap: 4px;
		padding: 0.5rem;
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

<script lang="ts">
	import { api } from '$lib/api';

	interface Token {
		symbol: string;
		chain: string;
		name: string;
	}

	interface Props {
		selectedToken?: string;
		selectedChain?: string;
		onSelect: (token: string, chain: string) => void;
		disabled?: boolean;
		label?: string;
	}

	let { selectedToken = '', selectedChain = '', onSelect, disabled = false, label = 'Select Token' }: Props = $props();

	let searchQuery = $state('');
	let isOpen = $state(false);
	let tokens = $state<Token[]>([]);
	let isLoading = $state(false);
	let inputEl: HTMLInputElement;
	let containerEl: HTMLDivElement;

	const commonTokens: Token[] = [
		{ symbol: 'BTC', chain: 'btc', name: 'Bitcoin' },
		{ symbol: 'ETH', chain: 'eth', name: 'Ethereum' },
		{ symbol: 'BNB', chain: 'bsc', name: 'BNB' },
		{ symbol: 'PEPE', chain: 'bsc', name: 'Pepe' },
		{ symbol: 'SHIB', chain: 'eth', name: 'Shiba Inu' },
		{ symbol: 'DOGE', chain: 'doge', name: 'Dogecoin' },
		{ symbol: 'SOL', chain: 'sol', name: 'Solana' },
		{ symbol: 'XRP', chain: 'xrp', name: 'Ripple' },
	];

	$effect(() => {
		function handleClickOutside(event: MouseEvent) {
			if (containerEl && !containerEl.contains(event.target as Node)) {
				isOpen = false;
			}
		}
		document.addEventListener('click', handleClickOutside);
		return () => document.removeEventListener('click', handleClickOutside);
	});

	async function loadTokens() {
		isLoading = true;
		try {
			tokens = await api.config.getTokens();
		} catch (e) {
			tokens = commonTokens;
		} finally {
			isLoading = false;
		}
	}

	function getFilteredTokens(): Token[] {
		const allTokens = tokens.length > 0 ? tokens : commonTokens;
		if (!searchQuery) return allTokens.slice(0, 10);
		const query = searchQuery.toLowerCase();
		return allTokens.filter(
			t => t.symbol.toLowerCase().includes(query) ||
				t.name.toLowerCase().includes(query) ||
				t.chain.toLowerCase().includes(query)
		).slice(0, 10);
	}

	function handleSelect(token: Token) {
		onSelect(token.symbol, token.chain);
		searchQuery = '';
		isOpen = false;
	}

	function handleInputFocus() {
		isOpen = true;
		if (tokens.length === 0 && !isLoading) {
			loadTokens();
		}
	}
</script>

<div class="token-picker" bind:this={containerEl}>
	{#if label}
		<label>{label}</label>
	{/if}
	
	<div class="input-wrapper">
		<input
			type="text"
			bind:this={inputEl}
			bind:value={searchQuery}
			onfocus={handleInputFocus}
			placeholder={selectedToken ? `${selectedToken}${selectedChain ? ` (${selectedChain})` : ''}` : 'Search tokens...'}
			{disabled}
			class:has-value={selectedToken}
		/>
		{#if selectedToken}
			<button class="clear-btn" onclick={() => onSelect('', '')} disabled={disabled}>
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>
		{/if}
	</div>

	{#if isOpen}
		<div class="dropdown">
			{#if isLoading}
				<div class="loading">Loading tokens...</div>
			{:else if getFilteredTokens().length === 0}
				<div class="no-results">No tokens found</div>
			{:else}
				{#each getFilteredTokens() as token}
					<button
						class="token-option"
						class:selected={token.symbol === selectedToken && token.chain === selectedChain}
						onclick={() => handleSelect(token)}
					>
						<span class="token-symbol">{token.symbol}</span>
						<span class="token-chain">{token.chain.toUpperCase()}</span>
						<span class="token-name">{token.name}</span>
					</button>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	.token-picker {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	label {
		font-size: 0.9rem;
		color: #888;
	}

	.input-wrapper {
		position: relative;
	}

	input {
		width: 100%;
		padding: 0.75rem 2.5rem 0.75rem 1rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
		box-sizing: border-box;
	}

	input:focus {
		outline: none;
		border-color: #667eea;
	}

	input.has-value {
		border-color: rgba(102, 126, 234, 0.5);
	}

	input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.clear-btn {
		position: absolute;
		right: 0.75rem;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		color: #888;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.clear-btn:hover:not(:disabled) {
		color: #fff;
	}

	.dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		margin-top: 0.5rem;
		background: #1a1a1a;
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		max-height: 250px;
		overflow-y: auto;
		z-index: 50;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
	}

	.loading,
	.no-results {
		padding: 1rem;
		text-align: center;
		color: #888;
		font-size: 0.9rem;
	}

	.token-option {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		color: #fff;
		text-align: left;
		cursor: pointer;
		transition: background 0.2s;
	}

	.token-option:hover {
		background: rgba(255, 255, 255, 0.05);
	}

	.token-option.selected {
		background: rgba(102, 126, 234, 0.2);
	}

	.token-symbol {
		font-weight: 600;
		min-width: 60px;
	}

	.token-chain {
		font-size: 0.75rem;
		padding: 0.15rem 0.4rem;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		color: #888;
	}

	.token-name {
		flex: 1;
		color: #888;
		font-size: 0.9rem;
	}
</style>
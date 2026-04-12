<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, currentBotStore, setCurrentBot, simulationStore, setCurrentSimulation, addSignals, clearSignals, setSimulationLoading, setSimulationError } from '$lib/stores';
	import { api } from '$lib/api';
	import { SignalChart } from '$lib/components';

	let botId = $derived($page.params.id);
	let tokenName = $state('');
	let tokenAddress = $state('');
	let intervalSeconds = $state(60);
	let isRunning = $state(false);

	onMount(async () => {
		if (!$isAuthenticated && !$isLoading) {
			goto('/login');
			return;
		}
		if ($isAuthenticated && botId) {
			await loadBot();
			await loadSimulations();
		}
	});

	async function loadBot() {
		try {
			const bot = await api.bots.get(botId);
			setCurrentBot(bot);
			
			// Extract token info from strategy config
			const strategy = bot.strategy_config;
			if (strategy) {
				const condition = strategy.conditions?.[0];
				const action = strategy.actions?.[0];
				tokenName = condition?.token || action?.token || '';
				tokenAddress = condition?.token_address || action?.token_address || '';
			}
		} catch (e) {
			goto('/dashboard');
		}
	}

	async function loadSimulations() {
		try {
			const simulations = await api.simulate.list(botId);
			if (simulations.length > 0) {
				const latest = simulations[0];
				setCurrentSimulation(latest);
				if (latest.signals) {
					addSignals(latest.signals);
				}
				if (latest.status === 'running') {
					isRunning = true;
				}
			}
		} catch (e) {
			console.error('Failed to load simulations:', e);
		}
	}

	async function startSimulation() {
		setSimulationError(null);
		setSimulationLoading(true);
		isRunning = true;

		try {
			const simulation = await api.simulate.start(botId, {
				token: tokenAddress,
				chain: 'bsc',
				check_interval: intervalSeconds
			});
			setCurrentSimulation(simulation);
			clearSignals();
		} catch (e) {
			setSimulationError(e instanceof Error ? e.message : 'Failed to start simulation');
			isRunning = false;
		} finally {
			setSimulationLoading(false);
		}
	}

	async function stopSimulation() {
		if (!$simulationStore.currentSimulation) return;
		
		try {
			await api.simulate.stop(botId, $simulationStore.currentSimulation.id);
			await loadSimulations();
			isRunning = false;
		} catch (e) {
			console.error('Failed to stop simulation:', e);
		}
	}
</script>

<svelte:head>
	<title>Simulate - {$currentBotStore?.name || 'Bot'} - Randebu</title>
</svelte:head>

<main>
	<header>
		<div class="header-left">
			<a href="/bot/{botId}" class="back-link">← Back to Chat</a>
			<h1>Simulation</h1>
		</div>
	</header>

	<div class="notice">
		<span class="notice-icon">⚠️</span>
		<span>Simulation Mode - Using REST polling (every {intervalSeconds}s). For real-time signals, consider upgrading to Pro tier.</span>
	</div>

	<div class="content">
		<section class="config-section">
			<h2>Configure Simulation</h2>
			
			{#if $simulationStore.error}
				<div class="error">{$simulationStore.error}</div>
			{/if}

			<form onsubmit={(e) => { e.preventDefault(); startSimulation(); }}>
				<div class="form-row">
					<div class="field token-info">
						<label>Token</label>
						<div class="token-display">
							<span class="token-name">{tokenName || 'Not configured'}</span>
							{#if tokenAddress}
								<span class="token-address">{tokenAddress.slice(0, 10)}...{tokenAddress.slice(-8)}</span>
							{/if}
						</div>
					</div>
					<div class="field">
						<label for="interval">Check Interval</label>
						<select id="interval" bind:value={intervalSeconds} disabled={isRunning}>
							<option value={10}>Every 10 seconds</option>
							<option value={30}>Every 30 seconds</option>
							<option value={60}>Every minute</option>
						</select>
					</div>
				</div>

				{#if isRunning}
					<button type="button" onclick={stopSimulation} class="btn btn-danger">
						Stop Simulation
					</button>
				{:else}
					<button type="submit" disabled={$simulationStore.isLoading}>
						{$simulationStore.isLoading ? 'Starting...' : 'Start Simulation'}
					</button>
				{/if}
			</form>
		</section>

		<section class="signals-section">
			<h2>Signals ({$simulationStore.signals.length})</h2>
			
			{#if $simulationStore.signals.length === 0}
				<p class="empty-state">No signals yet. Start a simulation to see trading signals.</p>
			{:else}
				<SignalChart signals={$simulationStore.signals} height={200} />
				
				<div class="signals-list">
					{#each $simulationStore.signals as signal}
						<div class="signal-card">
							<div class="signal-header">
								<span class="signal-type type-{signal.signal_type}">{signal.signal_type}</span>
								<span class="signal-token">{signal.token}</span>
								<span class="signal-price">${signal.price.toFixed(6)}</span>
							</div>
							{#if signal.confidence}
								<div class="signal-confidence">
									<span>Confidence: {(signal.confidence * 100).toFixed(1)}%</span>
									<div class="confidence-bar">
										<div class="confidence-fill" style="width: {signal.confidence * 100}%"></div>
									</div>
								</div>
							{/if}
							{#if signal.reasoning}
								<p class="signal-reasoning">{signal.reasoning}</p>
							{/if}
							<div class="signal-time">
								{new Date(signal.created_at).toLocaleString()}
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</section>
	</div>
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
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		margin-bottom: 1.5rem;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.back-link {
		color: #667eea;
		text-decoration: none;
		font-size: 0.9rem;
	}

	h1 {
		margin: 0;
		font-size: 1.75rem;
	}

	.notice {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: rgba(251, 191, 36, 0.1);
		border: 1px solid rgba(251, 191, 36, 0.3);
		border-radius: 8px;
		padding: 0.75rem 1rem;
		margin-bottom: 1.5rem;
		font-size: 0.9rem;
		color: #fbbf24;
	}

	.notice-icon {
		font-size: 1.25rem;
	}

	.content {
		display: grid;
		gap: 2rem;
	}

	section {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
	}

	h2 {
		font-size: 1.25rem;
		margin: 0 0 1rem;
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

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.token-display {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		padding: 0.75rem;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 8px;
	}

	.token-name {
		font-weight: 600;
		color: #667eea;
	}

	.token-address {
		font-size: 0.8rem;
		color: #888;
		font-family: 'Monaco', 'Menlo', monospace;
	}

	.checkbox-field {
		flex-direction: row;
		align-items: center;
		margin-bottom: 1rem;
	}

	.checkbox-field input {
		width: auto;
		margin-right: 0.5rem;
	}

	.checkbox-field label {
		margin: 0;
	}

	label {
		font-size: 0.9rem;
		color: #ccc;
	}

	input, select {
		padding: 0.75rem;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.2);
		background: rgba(255, 255, 255, 0.05);
		color: #fff;
		font-size: 1rem;
	}

	input:focus, select:focus {
		outline: none;
		border-color: #667eea;
	}

	button {
		width: 100%;
		padding: 0.875rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: transform 0.2s;
	}

	button:hover:not(:disabled) {
		transform: translateY(-2px);
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-danger {
		background: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
		border: 1px solid rgba(239, 68, 68, 0.4);
	}

	.empty-state {
		color: #888;
		text-align: center;
		padding: 2rem;
	}

	.signals-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.signal-card {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 8px;
		padding: 1rem;
	}

	.signal-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 0.5rem;
	}

	.signal-type {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.type-buy {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}

	.type-sell {
		background: rgba(239, 68, 68, 0.2);
		color: #ef4444;
	}

	.type-hold {
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
	}

	.signal-token {
		font-weight: 500;
	}

	.signal-price {
		color: #888;
		font-size: 0.9rem;
	}

	.signal-confidence {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
		font-size: 0.85rem;
		color: #888;
	}

	.confidence-bar {
		flex: 1;
		height: 4px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
	}

	.confidence-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea, #764ba2);
		border-radius: 2px;
	}

	.signal-reasoning {
		font-size: 0.9rem;
		color: #ccc;
		margin: 0.5rem 0;
		line-height: 1.4;
	}

	.signal-time {
		font-size: 0.75rem;
		color: #666;
	}
</style>

<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading, currentBotStore, setCurrentBot, backtestStore, setCurrentBacktest, addBacktestToHistory, setBacktestLoading, setBacktestError } from '$lib/stores';
	import { api } from '$lib/api';
	import { BacktestChart } from '$lib/components';
	import type { Backtest } from '$lib/api';

	let botId = $derived($page.params.id);
	let token = $state('PEPE');
	let timeframe = $state('1h');
	let startDate = $state('');
	let endDate = $state('');
	let isRunning = $state(false);
	let selectedBacktest = $state<Backtest | null>(null);

	onMount(async () => {
		// Set default dates (yesterday to 30 days ago)
		const yesterday = new Date();
		yesterday.setDate(yesterday.getDate() - 1);
		const thirtyDaysAgo = new Date();
		thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
		
		endDate = yesterday.toISOString().split('T')[0];
		startDate = thirtyDaysAgo.toISOString().split('T')[0];
		
		if (!$isAuthenticated && !$isLoading) {
			goto('/login');
			return;
		}
		if ($isAuthenticated && botId) {
			await loadBot();
			await loadBacktests();
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

	async function loadBacktests() {
		try {
			const backtests = await api.backtest.list(botId);
			setBacktestHistory(backtests);
		} catch (e) {
			console.error('Failed to load backtests:', e);
		}
	}

	async function startBacktest() {
		if (!startDate || !endDate) return;
		setBacktestError(null);
		setBacktestLoading(true);
		isRunning = true;

		try {
			const backtest = await api.backtest.start(botId, {
				token,
				timeframe,
				start_date: startDate,
				end_date: endDate
			});
			setCurrentBacktest(backtest);
			addBacktestToHistory(backtest);
		} catch (e) {
			setBacktestError(e instanceof Error ? e.message : 'Failed to start backtest');
		} finally {
			setBacktestLoading(false);
			isRunning = false;
		}
	}

	async function stopBacktest(runId: string) {
		try {
			await api.backtest.stop(botId, runId);
			await loadBacktests();
		} catch (e) {
			console.error('Failed to stop backtest:', e);
		}
	}

	function setBacktestHistory(backtests: any[]) {
		backtestStore.update(state => ({ ...state, backtestHistory: backtests }));
	}

	function selectBacktest(backtest: Backtest) {
		if (backtest.status === 'completed' && backtest.result && !backtest.result.error) {
			selectedBacktest = backtest;
		}
	}
</script>

<svelte:head>
	<title>Backtest - {$currentBotStore?.name || 'Bot'} - Randebu</title>
</svelte:head>

<main>
	<header>
		<div class="header-left">
			<a href="/bot/{botId}" class="back-link">← Back to Chat</a>
			<h1>Backtest</h1>
		</div>
	</header>

	<div class="content">
		<section class="config-section">
			<h2>Configure Backtest</h2>
			
			{#if $backtestStore.error}
				<div class="error">{$backtestStore.error}</div>
			{/if}

			<form onsubmit={(e) => { e.preventDefault(); startBacktest(); }}>
				<div class="form-row">
					<div class="field">
						<label for="token">Token</label>
						<input type="text" id="token" bind:value={token} required />
					</div>
					<div class="field">
						<label for="timeframe">Timeframe</label>
						<select id="timeframe" bind:value={timeframe}>
							<option value="1m">1 minute</option>
							<option value="5m">5 minutes</option>
							<option value="15m">15 minutes</option>
							<option value="1h">1 hour</option>
							<option value="4h">4 hours</option>
							<option value="1d">1 day</option>
						</select>
					</div>
				</div>

				<div class="form-row">
					<div class="field">
						<label for="startDate">Start Date</label>
						<input type="date" id="startDate" bind:value={startDate} required />
					</div>
					<div class="field">
						<label for="endDate">End Date</label>
						<input type="date" id="endDate" bind:value={endDate} required />
					</div>
				</div>

				<button type="submit" disabled={isRunning || $backtestStore.isLoading}>
					{isRunning ? 'Running...' : 'Start Backtest'}
				</button>
			</form>
		</section>

		<section class="results-section">
			<div class="section-header">
				<h2>Backtest History</h2>
				<button class="btn-refresh" onclick={() => loadBacktests()} disabled={$backtestStore.isLoading}>
					{$backtestStore.isLoading ? 'Refreshing...' : 'Refresh'}
				</button>
			</div>
			
			{#if $backtestStore.backtestHistory.length === 0}
				<p class="empty-state">No backtests yet. Run your first backtest above.</p>
			{:else}
				<div class="backtest-list">
					{#each $backtestStore.backtestHistory as backtest}
						<div class="backtest-card">
							<div class="backtest-header">
								<span class="backtest-status status-{backtest.status}">{backtest.status}</span>
								<span class="backtest-date">{new Date(backtest.started_at).toLocaleDateString()}</span>
							</div>
							{#if backtest.result && backtest.result.error}
							<div class="backtest-error">
								<span class="error-label">Error:</span> {typeof backtest.result.error === 'string' ? backtest.result.error : JSON.stringify(backtest.result.error)}
							</div>
						{:else if backtest.result}
								<div class="backtest-results">
									<div class="result-item">
										<span class="result-label">Total Return</span>
										<span class="result-value" class:positive={backtest.result.total_return > 0} class:negative={backtest.result.total_return < 0}>
											{backtest.result.total_return.toFixed(2)}%
										</span>
									</div>
									<div class="result-item">
										<span class="result-label">Win Rate</span>
										<span class="result-value">{backtest.result.win_rate.toFixed(1)}%</span>
									</div>
									<div class="result-item">
										<span class="result-label">Total Trades</span>
										<span class="result-value">{backtest.result.total_trades}</span>
									</div>
									<div class="result-item">
										<span class="result-label">Max Drawdown</span>
										<span class="result-value negative">{backtest.result.max_drawdown.toFixed(2)}%</span>
									</div>
								</div>
							{/if}
							{#if backtest.status === 'running'}
								<div class="progress-container">
									<div class="progress-bar">
										<div class="progress-fill" style="width: {backtest.progress ?? 0}%"></div>
									</div>
									<span class="progress-text">{backtest.progress ?? 0}%</span>
								</div>
								<button onclick={() => stopBacktest(backtest.id)} class="btn btn-danger">Stop</button>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</section>

		{#if selectedBacktest}
			<section class="chart-section">
				<div class="chart-header">
					<h2>Portfolio Performance</h2>
					<button class="close-btn" onclick={() => selectedBacktest = null}>×</button>
				</div>
				<BacktestChart results={selectedBacktest.result} />
			</section>
		{/if}
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
		margin-bottom: 2rem;
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

	h2 {
		font-size: 1.25rem;
		margin: 0;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.section-header h2 {
		margin: 0;
	}

	.btn-refresh {
		padding: 0.5rem 1rem;
		background: rgba(255, 255, 255, 0.1);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 6px;
		font-size: 0.85rem;
		cursor: pointer;
		width: auto;
	}

	.btn-refresh:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.15);
		transform: none;
	}

	.btn-refresh:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
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

	.error {
		background: rgba(239, 68, 68, 0.2);
		border: 1px solid #ef4444;
		color: #fca5a5;
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.backtest-error {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #fca5a5;
		padding: 0.75rem;
		border-radius: 8px;
		font-size: 0.85rem;
		margin-bottom: 0.75rem;
	}

	.error-label {
		font-weight: 600;
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

	.empty-state {
		color: #888;
		text-align: center;
		padding: 2rem;
	}

	.backtest-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.backtest-card {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 8px;
		padding: 1rem;
	}

	.backtest-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}

	.backtest-status {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}

	.status-running {
		background: rgba(59, 130, 246, 0.2);
		color: #60a5fa;
	}

	.status-completed {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}

	.status-failed {
		background: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
	}

	.status-stopped {
		background: rgba(251, 191, 36, 0.2);
		color: #fbbf24;
	}

	.backtest-date {
		color: #888;
		font-size: 0.85rem;
	}

	.backtest-results {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	.result-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.result-label {
		font-size: 0.75rem;
		color: #888;
	}

	.result-value {
		font-size: 1.1rem;
		font-weight: 500;
	}

	.positive {
		color: #22c55e;
	}

	.negative {
		color: #ef4444;
	}

	.progress-container {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.progress-bar {
		flex: 1;
		height: 8px;
		background: rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.85rem;
		color: #888;
		min-width: 40px;
	}

	.btn-danger {
		margin-top: 0.75rem;
		width: auto;
		padding: 0.5rem 1rem;
		background: rgba(239, 68, 68, 0.2);
		color: #fca5a5;
		border: 1px solid rgba(239, 68, 68, 0.4);
	}

	.chart-section {
		padding: 1.5rem;
	}

	.chart-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.chart-header h2 {
		margin: 0;
	}

	.close-btn {
		width: auto;
		padding: 0.25rem 0.75rem;
		background: rgba(255, 255, 255, 0.1);
		border: none;
		color: #888;
		font-size: 1.5rem;
		line-height: 1;
		cursor: pointer;
		border-radius: 4px;
	}

	.close-btn:hover {
		background: rgba(255, 255, 255, 0.2);
		color: #fff;
	}
</style>

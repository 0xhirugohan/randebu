<script lang="ts">
	import { isAuthenticated } from '$lib/stores';
</script>

<svelte:head>
	<title>Randebu - AI Trading Bot Platform</title>
</svelte:head>

{#if $isAuthenticated}
	<script>
		window.location.href = '/dashboard';
	</script>
{:else}
	<main>
		<div class="hero">
			<h1>Randebu</h1>
			<p class="tagline">Create trading bots through conversation with AI</p>
			<div class="cta">
				<a href="/register" class="btn btn-primary">Get Started</a>
				<a href="/login" class="btn btn-secondary">Login</a>
			</div>
		</div>

		<section class="features">
			<h2>How It Works</h2>
			<div class="feature-grid">
				<div class="feature">
					<h3>1. Describe Your Strategy</h3>
					<p>Tell our AI what kind of trading you want to do in plain English</p>
				</div>
				<div class="feature">
					<h3>2. Backtest & Validate</h3>
					<p>Test your strategy against historical data before risking real funds</p>
				</div>
				<div class="feature">
					<h3>3. Simulate & Monitor</h3>
					<p>Run real-time simulations and watch for trading signals</p>
				</div>
			</div>
		</section>
	</main>
{/if}

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		background: #0f0f0f;
		color: #fff;
	}

	main {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.hero {
		text-align: center;
		max-width: 600px;
	}

	h1 {
		font-size: 3.5rem;
		margin: 0;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.tagline {
		font-size: 1.25rem;
		color: #aaa;
		margin: 1rem 0 2rem;
	}

	.cta {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	.btn {
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 500;
		transition: transform 0.2s, opacity 0.2s;
	}

	.btn:hover {
		transform: translateY(-2px);
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

	.features {
		margin-top: 4rem;
		text-align: center;
	}

	.features h2 {
		font-size: 2rem;
		margin-bottom: 2rem;
	}

	.feature-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 2rem;
		max-width: 800px;
	}

	.feature h3 {
		font-size: 1.25rem;
		margin-bottom: 0.5rem;
	}

	.feature p {
		color: #888;
		font-size: 0.9rem;
	}
</style>

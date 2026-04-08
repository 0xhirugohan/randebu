<script lang="ts">
	import { goto } from '$app/navigation';
	import { login, isAuthenticated } from '$lib/stores';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let isLoading = $state(false);

	$effect(() => {
		if ($isAuthenticated) {
			goto('/dashboard');
		}
	});

	async function handleSubmit() {
		error = '';
		isLoading = true;
		try {
			await login(email, password);
			goto('/dashboard');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Login failed';
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - Randebu</title>
</svelte:head>

<main>
	<div class="auth-card">
		<h1>Login</h1>
		<p class="subtitle">Welcome back</p>

		{#if error}
			<div class="error">{error}</div>
		{/if}

		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
			<div class="field">
				<label for="email">Email</label>
				<input type="email" id="email" bind:value={email} required />
			</div>

			<div class="field">
				<label for="password">Password</label>
				<input type="password" id="password" bind:value={password} required />
			</div>

			<button type="submit" disabled={isLoading}>
				{isLoading ? 'Logging in...' : 'Login'}
			</button>
		</form>

		<p class="footer">
			Don't have an account? <a href="/register">Register</a>
		</p>
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
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.auth-card {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 16px;
		padding: 2.5rem;
		width: 100%;
		max-width: 400px;
	}

	h1 {
		margin: 0;
		font-size: 1.75rem;
		text-align: center;
	}

	.subtitle {
		color: #888;
		text-align: center;
		margin: 0.5rem 0 2rem;
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
		margin-bottom: 1.25rem;
	}

	label {
		display: block;
		margin-bottom: 0.5rem;
		color: #ccc;
		font-size: 0.9rem;
	}

	input {
		width: 100%;
		padding: 0.75rem;
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

	.footer {
		text-align: center;
		margin-top: 1.5rem;
		color: #888;
		font-size: 0.9rem;
	}

	.footer a {
		color: #667eea;
		text-decoration: none;
	}

	.footer a:hover {
		text-decoration: underline;
	}
</style>
